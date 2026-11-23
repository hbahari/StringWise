from stringwise.content import settings
from stringwise.content.tour import STEPS

TARGETS = {"tuner_dial", "metronome", "header_metronome", "week_chips", "fingerboard",
           "theory", "rhythm", "gear"}
SCREENS = {"tuner", "metronome", "lessons", "fingers", "theory", "practice"}


def test_tour_steps_are_well_formed():
    assert STEPS[0].target is None and STEPS[-1].target is None      # welcome and finish
    for step in STEPS[1:-1]:
        assert step.target in TARGETS
        assert step.screen is None or step.screen in SCREENS
        assert step.tab is None or step.tab == step.screen
        assert len(step.text) < 260, step.title                    # fits in the bubble on a phone
    assert len({s.target for s in STEPS[1:-1]}) == len(STEPS) - 2
    assert {s.screen for s in STEPS if s.screen} == SCREENS             # every tab is visited


def test_share_message_has_the_store_link():
    assert settings.STORE_WEB_LINK in settings.SHARE_MESSAGE
    assert settings.SHARE_MESSAGE.startswith("I'm learning violin")
