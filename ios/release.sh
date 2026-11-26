#!/bin/bash
# Archive a signed StringWise build and upload it to App Store Connect (TestFlight).
# For later, once the Apple Developer account exists. Run ios/build.sh first.
#
# Signing is automatic: Xcode uses an App Store Connect API key to create the
# certificate and profile itself, so no certificate files need to be kept.
#
# Needs these environment variables (GitHub secrets in the workflow):
#   IOS_TEAM_ID            10-character Team ID from developer.apple.com > Membership
#   APP_STORE_API_KEY_ID   Key ID of an App Store Connect API key with the Admin role
#   APP_STORE_API_ISSUER   Issuer ID shown above the list of keys
#   APP_STORE_API_KEY_P8   the contents of the downloaded AuthKey_XXXX.p8 file
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$HERE/build"
PROJECT="$WORK/kivy-ios/stringwise-ios/stringwise.xcodeproj"
: "${IOS_TEAM_ID:?}" "${APP_STORE_API_KEY_ID:?}" "${APP_STORE_API_ISSUER:?}" "${APP_STORE_API_KEY_P8:?}"

KEY_FILE="$WORK/AuthKey_${APP_STORE_API_KEY_ID}.p8"
printf '%s\n' "$APP_STORE_API_KEY_P8" > "$KEY_FILE"
chmod 600 "$KEY_FILE"
trap 'rm -f "$KEY_FILE"' EXIT

AUTH=(-allowProvisioningUpdates
      -authenticationKeyPath "$KEY_FILE"
      -authenticationKeyID "$APP_STORE_API_KEY_ID"
      -authenticationKeyIssuerID "$APP_STORE_API_ISSUER")

rm -rf "$WORK/StringWise.xcarchive" "$WORK/export"
xcodebuild -project "$PROJECT" -scheme stringwise -configuration Release \
    -destination 'generic/platform=iOS' -archivePath "$WORK/StringWise.xcarchive" \
    DEVELOPMENT_TEAM="$IOS_TEAM_ID" CODE_SIGN_STYLE=Automatic \
    "${AUTH[@]}" archive

cat > "$WORK/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key><string>app-store-connect</string>
    <key>destination</key><string>upload</string>
    <key>teamID</key><string>${IOS_TEAM_ID}</string>
    <key>signingStyle</key><string>automatic</string>
    <key>uploadSymbols</key><true/>
    <key>manageAppVersionAndBuildNumber</key><false/>
</dict>
</plist>
PLIST

# With destination "upload", exporting sends the build straight to App Store Connect.
xcodebuild -exportArchive -archivePath "$WORK/StringWise.xcarchive" \
    -exportOptionsPlist "$WORK/ExportOptions.plist" -exportPath "$WORK/export" \
    "${AUTH[@]}"
echo "Uploaded. It appears in App Store Connect > TestFlight after Apple processes it (often 10-30 minutes)."
