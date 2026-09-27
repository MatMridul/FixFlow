"""URL detection and scrubbing utilities to prevent external web URL leakage."""
import re
from schema import Action, Goal, StepGroup

# Regex patterns for web URLs and markdown links
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\((?:https?://|www\.)[^\s\)]+\)', re.IGNORECASE)
RAW_URL_PATTERN = re.compile(r'(?:https?://|www\.)[^\s<>"\'\)]+', re.IGNORECASE)
SCHEME_URL_PATTERN = re.compile(r'https?://[^\s]+', re.IGNORECASE)
# FAQ Q6 counts ".com", ".html", markdown images and link tags as URL leaks
# too (gate G5: zero leaks) — e.g. an LLM writing "Visit samsung.com/support".
BARE_DOMAIN_PATTERN = re.compile(
    r'\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|co|io|html?)\b(?:/[^\s<>"\')]*)?', re.IGNORECASE
)
MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[[^\]]*\]\([^)]*\)')
LINK_TAG_PATTERN = re.compile(r'<\s*/?\s*a\b[^>]*>', re.IGNORECASE)


def contains_urls(text: str) -> bool:
    """Check for anything the scorer treats as a URL leak: http(s), www., bare
    .com/.html domains, markdown links/images, and <a> link tags."""
    if not text:
        return False
    return bool(
        MARKDOWN_LINK_PATTERN.search(text)
        or RAW_URL_PATTERN.search(text)
        or SCHEME_URL_PATTERN.search(text)
        or BARE_DOMAIN_PATTERN.search(text)
        or MARKDOWN_IMAGE_PATTERN.search(text)
        or LINK_TAG_PATTERN.search(text)
    )


def scrub_urls(text: str) -> str:
    """
    Remove external web URLs and markdown web link wrappers from text.
    Replaces '[Anchor Text](http://...)' with 'Anchor Text' and removes bare URLs.
    """
    if not text:
        return text

    # First, drop images and replace markdown link wrappers with just the anchor text
    cleaned = MARKDOWN_IMAGE_PATTERN.sub('', text)
    cleaned = MARKDOWN_LINK_PATTERN.sub(r'\1', cleaned)
    cleaned = LINK_TAG_PATTERN.sub('', cleaned)

    # Second, remove raw URLs and bare domains
    cleaned = RAW_URL_PATTERN.sub('', cleaned)
    cleaned = BARE_DOMAIN_PATTERN.sub('', cleaned)

    # Clean up excess whitespace and dangling punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\s+([,.:;?!])', r'\1', cleaned)
    return cleaned


def scrub_step_group(step_group: StepGroup) -> StepGroup:
    """Scrub external URLs from all steps within a StepGroup."""
    scrubbed_steps = [scrub_urls(step) for step in step_group.steps]
    step_group.steps = scrubbed_steps
    return step_group


def scrub_action(action: Action) -> Action:
    """Scrub external URLs from actionName, description, and nested steps."""
    action.actionName = scrub_urls(action.actionName)
    action.description = scrub_urls(action.description)
    for sg in action.stepGroups:
        scrub_step_group(sg)
    return action


def scrub_goal(goal: Goal) -> Goal:
    """Scrub external URLs from all fields across the entire Goal hierarchy."""
    goal.goal = scrub_urls(goal.goal)
    goal.title = scrub_urls(goal.title)
    for action in goal.actions:
        scrub_action(action)
    return goal
