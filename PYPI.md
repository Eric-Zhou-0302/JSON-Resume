# JSON-Resume

Generate a polished DOCX resume from strict, structured JSON.

`json-resume` validates your resume data before rendering, applies a stable Word layout with locale-aware paper sizes, and provides both a command-line tool and Python APIs. It is designed for repeatable resume generation in local scripts, automation, and backend services.

## Install

```bash
python -m pip install json-resume
```

The package installs its DOCX and PDF-related Python dependencies together. PDF export uses local Microsoft Word through `docx2pdf`.

## Command line

Create a JSON resume, then generate a DOCX:

```bash
json-resume resume.json
```

By default, output is written to `output/resume.docx` under the current working directory. Common options:

```bash
json-resume resume.json -o resume.docx
json-resume resume.json --pdf
json-resume resume.json -o resume.docx --force
```

`--pdf` additionally writes a sibling PDF after DOCX generation. `--force` is required before replacing an existing DOCX or PDF.

## Python API

Use the file-level API in scripts and automation:

```python
from resume_generator import render_json_file_to_docx

output_path = render_json_file_to_docx(
    "resume.json",
    "resume.docx",
)

print(output_path)
```

Use the in-memory API in HTTP services or other integrations:

```python
from resume_generator import render_json_to_docx

docx_bytes = render_json_to_docx(data)
```

Both APIs use the same strict validation and rendering core as the CLI. Validation failures raise `FieldError` with a precise JSON source path.

## JSON contract

The top-level JSON object must contain exactly `locale`, `basics`, and `sections`.

```json
{
  "locale": "en-US",
  "basics": {
    "name": "Example Candidate",
    "contacts": [
      {
        "label": "candidate@example.com",
        "href": "mailto:candidate@example.com"
      }
    ]
  },
  "sections": [
    {
      "title": "Experience",
      "entries": [
        {
          "title": "Example Organization",
          "position": "Analyst Intern",
          "location": "New York, NY",
          "start_date": "2025-06",
          "end_date": "Present",
          "bullets": [
            "Completed a fact-supported contribution."
          ]
        }
      ]
    }
  ]
}
```

Supported locales are `zh-CN`, `en-US`, `en-GB`, and `en-EU`. `en-US` produces Letter paper; the others produce A4. Locale controls paper size only and does not translate content.

Read the full [JSON contract, examples, and usage guide](https://github.com/Eric-Zhou-0302/JSON-Resume#how-to-use).

## Project links

- [Source code](https://github.com/Eric-Zhou-0302/JSON-Resume)
- [Changelog](https://github.com/Eric-Zhou-0302/JSON-Resume/blob/main/CHANGELOG.md)
- [Issue tracker](https://github.com/Eric-Zhou-0302/JSON-Resume/issues)
- [MIT License](https://github.com/Eric-Zhou-0302/JSON-Resume/blob/main/LICENSE)
