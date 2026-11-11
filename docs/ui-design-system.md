# UI Design System

AASL uses a semantic typography system rather than one-off pixel values.

## Typography scale

The scale is anchored at a 16px body size and follows a **Major Third (1.25) modular scale** for headings, with rounded support sizes for labels and microcopy.

| Token | Size | Intended use |
| --- | ---: | --- |
| `--type-micro` | 12px | metadata, tags, keyboard hints |
| `--type-label` | 13px | labels, secondary text, code metadata |
| `--type-body` | 16px | primary reading text |
| `--type-body-lg` | 18px | questions and emphasized body copy |
| `--type-h3` | 20px | card / subsection headings |
| `--type-h2` | 25px | section headings |
| `--type-h1` | 31px | page headings |
| `--type-display` | 39px | reserved display use |

Line-height tokens:

- `--leading-tight` — headings;
- `--leading-normal` — normal UI/body text;
- `--leading-relaxed` — long-form or instructional text.

## Rule

No intentional UI text should render below the `--type-micro` token.

Legacy selectors are normalized at the end of the stylesheet so older component rules cannot reintroduce 8–11px text islands.

## Semantic mapping

Examples:

- navigation → body;
- questions → body-large;
- card titles → H3;
- section titles → H2;
- page titles → H1;
- tags/IDs/meta → micro;
- labels/supporting copy → label/body as appropriate;
- artifacts/JSON/code → label with increased line height.

This keeps the dense security-console visual style without sacrificing readability.
