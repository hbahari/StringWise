/*
 * Microphone input for StringWise on iOS.
 *
 * A RemoteIO audio unit records mono float samples. The audio thread only copies
 * them into a lock-free ring buffer (swmic_ring.h); Python drains the buffer from its own
 * thread with swmic_read(), so Python never runs on the real-time audio thread.
 *
 * The audio session is set to PlayAndRecord with the same options SDL2 uses
 * when the SDL_AUDIO_CATEGORY hint asks for PlayAndRecord. Keeping the two in
 * step means SDL does not reset the session when Kivy plays a sound, so the
 * metronome and the microphone can run together.
 */

#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
#import <AudioToolbox/AudioToolbox.h>
#include <stdatomic.h>
#include "swmic_ios.h"
#include "swmic_ring.h"

#define MAX_FRAMES 8192              /* largest render slice iOS asks for */

static float scratch[MAX_FRAMES];
static AudioComponentInstance unit = NULL;
static atomic_int running = 0;
static atomic_int permission_answer = -1;   /* -1 until the dialog is answered */
static id interruption_observer = nil;

/* Same options SDL2 picks for PlayAndRecord: mix with others, duck others,
   Bluetooth, default to speaker, A2DP and AirPlay. */
static const AVAudioSessionCategoryOptions SESSION_OPTIONS =
    AVAudioSessionCategoryOptionMixWithOthers |
    AVAudioSessionCategoryOptionDuckOthers |
    AVAudioSessionCategoryOptionAllowBluetooth |
    AVAudioSessionCategoryOptionDefaultToSpeaker |
    AVAudioSessionCategoryOptionAllowBluetoothA2DP |
    AVAudioSessionCategoryOptionAllowAirPlay;

int swmic_configure_session(void) {
    @autoreleasepool {
        AVAudioSession *session = [AVAudioSession sharedInstance];
        NSError *error = nil;
        if (![session.category isEqualToString:AVAudioSessionCategoryPlayAndRecord] ||
                session.categoryOptions != SESSION_OPTIONS) {
            if (![session setCategory:AVAudioSessionCategoryPlayAndRecord
                                 mode:AVAudioSessionModeDefault
                              options:SESSION_OPTIONS
                                error:&error]) {
                NSLog(@"swmic: setCategory failed: %@", error);
                return -1;
            }
        }
        [session setPreferredSampleRate:44100.0 error:nil];
        [session setPreferredIOBufferDuration:0.010 error:nil];
        if (![session setActive:YES error:&error]) {
            NSLog(@"swmic: setActive failed: %@", error);
            return -2;
        }
        return 0;
    }
}

int swmic_permission(void) {
    int answer = atomic_load(&permission_answer);
    if (answer >= 0) {
        return answer ? SWMIC_GRANTED : SWMIC_DENIED;
    }
    if (@available(iOS 17.0, *)) {
        switch ([[AVAudioApplication sharedInstance] recordPermission]) {
            case AVAudioApplicationRecordPermissionGranted: return SWMIC_GRANTED;
            case AVAudioApplicationRecordPermissionDenied: return SWMIC_DENIED;
            default: return SWMIC_UNKNOWN;
        }
    }
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    switch ([[AVAudioSession sharedInstance] recordPermission]) {
        case AVAudioSessionRecordPermissionGranted: return SWMIC_GRANTED;
        case AVAudioSessionRecordPermissionDenied: return SWMIC_DENIED;
        default: return SWMIC_UNKNOWN;
    }
#pragma clang diagnostic pop
}

void swmic_request_permission(void) {
    atomic_store(&permission_answer, -1);
    void (^answered)(BOOL) = ^(BOOL granted) {
        atomic_store(&permission_answer, granted ? 1 : 0);
    };
    if (@available(iOS 17.0, *)) {
        [AVAudioApplication requestRecordPermissionWithCompletionHandler:answered];
        return;
    }
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    [[AVAudioSession sharedInstance] requestRecordPermission:answered];
#pragma clang diagnostic pop
}

static OSStatus on_input(void *ref, AudioUnitRenderActionFlags *flags,
                         const AudioTimeStamp *stamp, UInt32 bus,
                         UInt32 frames, AudioBufferList *unused) {
    if (frames > MAX_FRAMES) {
        frames = MAX_FRAMES;
    }
    AudioBufferList list;
    list.mNumberBuffers = 1;
    list.mBuffers[0].mNumberChannels = 1;
    list.mBuffers[0].mDataByteSize = frames * sizeof(float);
    list.mBuffers[0].mData = scratch;
    OSStatus status = AudioUnitRender(unit, flags, stamp, bus, frames, &list);
    if (status != noErr) {
        return status;
    }
    ring_push(scratch, frames);
    return noErr;
}

int swmic_read(float *out, int max_count) {
    return ring_pop(out, max_count);
}

static void dispose_unit(void) {
    if (unit != NULL) {
        AudioOutputUnitStop(unit);
        AudioUnitUninitialize(unit);
        AudioComponentInstanceDispose(unit);
        unit = NULL;
    }
}

int swmic_start(double sample_rate) {
    if (atomic_load(&running)) {
        return 0;
    }
    if (swmic_configure_session() != 0) {
        return -1;
    }
    AudioComponentDescription desc = {0};
    desc.componentType = kAudioUnitType_Output;
    desc.componentSubType = kAudioUnitSubType_RemoteIO;
    desc.componentManufacturer = kAudioUnitManufacturer_Apple;
    AudioComponent component = AudioComponentFindNext(NULL, &desc);
    if (component == NULL || AudioComponentInstanceNew(component, &unit) != noErr) {
        unit = NULL;
        return -2;
    }

    UInt32 on = 1, off = 0;
    /* Bus 1 is the microphone, bus 0 the speaker. We only record; Kivy plays sound through SDL. */
    AudioUnitSetProperty(unit, kAudioOutputUnitProperty_EnableIO, kAudioUnitScope_Input, 1, &on, sizeof(on));
    AudioUnitSetProperty(unit, kAudioOutputUnitProperty_EnableIO, kAudioUnitScope_Output, 0, &off, sizeof(off));

    UInt32 max_frames = MAX_FRAMES;
    AudioUnitSetProperty(unit, kAudioUnitProperty_MaximumFramesPerSlice, kAudioUnitScope_Global, 0,
                         &max_frames, sizeof(max_frames));

    /* Ask for mono float at our rate; RemoteIO converts from the hardware rate if it differs. */
    AudioStreamBasicDescription format = {0};
    format.mSampleRate = sample_rate;
    format.mFormatID = kAudioFormatLinearPCM;
    format.mFormatFlags = kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked | kAudioFormatFlagIsNonInterleaved;
    format.mChannelsPerFrame = 1;
    format.mBitsPerChannel = 32;
    format.mBytesPerFrame = 4;
    format.mFramesPerPacket = 1;
    format.mBytesPerPacket = 4;
    if (AudioUnitSetProperty(unit, kAudioUnitProperty_StreamFormat, kAudioUnitScope_Output, 1,
                             &format, sizeof(format)) != noErr) {
        dispose_unit();
        return -3;
    }

    AURenderCallbackStruct callback = {on_input, NULL};
    if (AudioUnitSetProperty(unit, kAudioOutputUnitProperty_SetInputCallback, kAudioUnitScope_Global, 1,
                             &callback, sizeof(callback)) != noErr) {
        dispose_unit();
        return -4;
    }
    if (AudioUnitInitialize(unit) != noErr) {
        dispose_unit();
        return -5;
    }

    ring_reset();
    if (AudioOutputUnitStart(unit) != noErr) {
        dispose_unit();
        return -6;
    }
    atomic_store(&running, 1);

    /* A phone call or Siri stops the unit. Start it again when the interruption ends. */
    if (interruption_observer == nil) {
        interruption_observer = [[NSNotificationCenter defaultCenter]
            addObserverForName:AVAudioSessionInterruptionNotification
                        object:nil
                         queue:[NSOperationQueue mainQueue]
                    usingBlock:^(NSNotification *note) {
            NSUInteger type = [note.userInfo[AVAudioSessionInterruptionTypeKey] unsignedIntegerValue];
            if (type == AVAudioSessionInterruptionTypeEnded && atomic_load(&running) && unit != NULL) {
                [[AVAudioSession sharedInstance] setActive:YES error:nil];
                AudioOutputUnitStart(unit);
            }
        }];
    }
    return 0;
}

void swmic_stop(void) {
    atomic_store(&running, 0);
    dispose_unit();
}

double swmic_hardware_rate(void) {
    return [[AVAudioSession sharedInstance] sampleRate];
}

int swmic_dropped(void) {
    return atomic_load(&ring_dropped);
}
