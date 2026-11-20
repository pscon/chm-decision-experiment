import pytest

from app.config import load_config


def write(tmp_path, text):
    path = tmp_path / "config.yml"
    path.write_text(text)
    return str(path)


def test_loads_valid_config(tmp_path):
    config = load_config(write(tmp_path, "participants: [human, ai, ai]\ndiscussion_seconds: 30\n"))
    assert config.participants == ("human", "ai", "ai")
    assert config.human_count == 1
    assert config.discussion_seconds == 30
    assert config.voting_seconds == 20  # default


@pytest.mark.parametrize(
    "text",
    [
        "participants: [human, human]",  # wrong count
        "participants: [human, robot, ai]",  # unknown type
        "participants: [ai, ai, ai]",  # no human
        "participants: [human, ai, ai]\nvoting_seconds: 2",  # too short
    ],
)
def test_rejects_invalid_config(tmp_path, text):
    with pytest.raises(ValueError):
        load_config(write(tmp_path, text))
