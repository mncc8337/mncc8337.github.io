import datetime
import subprocess
from shutil import copytree, rmtree
from pathlib import Path
from typing import Any

import frontmatter
from markdown_it.presets import gfm_like
from markdown_it import MarkdownIt
from markdown_it.token import Token
import jinja2


TIME_FORMAT = "%d %b %Y %H:%M"


def get_time_now() -> str:
    return datetime.datetime.now().strftime(TIME_FORMAT)


def parse_strftime(date_str: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(date_str, "%d %b %Y %H:%M")
    except ValueError:
        return datetime.datetime.strptime(date_str, "%d %b %Y")


def get_last_updated_time(file_path: Path) -> str:
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ['git', 'log', '-1', '--format=%cI', '--', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        date_str: str = result.stdout.strip()

        if date_str:
            return datetime.datetime.fromisoformat(date_str).strftime(TIME_FORMAT)

    except subprocess.CalledProcessError:
        pass

    return get_time_now()


def navbar_generator(nav_items: dict[str, bool]) -> str:
    out: str = ""

    for nav in nav_items.keys():
        if nav_items[nav]:
            out += f"<span class=\"left\">{nav}</span>\n"
        else:
            href: str = "/index.html" if nav == "main" else f"/{nav}/index.html"
            out += f"<a class=\"left\" href=\"{href}\">{nav}</a>\n"
    return out


def parse_writeup(
    md: MarkdownIt,
    nav_items: dict[str, bool],
    path: Path,
    content: str,
    metadata: dict,
    site_map: list[dict[str, Any]],
    hidden_nav: list[str]
) -> str:
    page_title: str = ""
    page_description: str = ""
    rendered_content: str = ""

    rel_path: Path = path.relative_to("pages/")
    category: str = rel_path.parts[0] if len(rel_path.parts) > 1 else "main"

    is_directory_index: bool = metadata.get("is_directory_index", False)
    nav_items_copy: dict[str, bool] = nav_items.copy()
    if category == "main" or is_directory_index or category in nav_hidden_list:
        nav_items_copy[category] = True

    if metadata.get("skip_md", False):
        rendered_content = content
        page_title = metadata.get("title", path.stem)
        page_description = metadata.get("description", "")
    else:
        tokens: list[Token] = md.parse(content)

        indices_to_drop: set[int] = set()

        # search and filter out page_title and page_description
        h1_end: int = -1
        h2_start: int = len(tokens)
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h1":
                page_title = tokens[i+1].content
                indices_to_drop.update([i, i+1, i+2])
                h1_end = i + 2
            elif token.type == "heading_open" and token.tag == "h2" and h1_end != -1:
                h2_start = i
                break

        if h1_end != -1:
            desc_tokens = [t for t in tokens[h1_end+1: h2_start]]
            page_description = md.renderer.render(desc_tokens, md.options, {})
            indices_to_drop.update([i for i in range(h1_end - 2, h2_start)])

        filtered_tokens: list[Token] = [
            t for i, t in enumerate(tokens) if i not in indices_to_drop
        ]

        is_below_header: bool = False
        for token in filtered_tokens:
            if is_below_header and token.type.endswith('_open'):
                token.attrJoin("class", "below-header")
                is_below_header = False

            is_below_header = token.type == "heading_close"

        rendered_content = md.renderer.render(filtered_tokens, md.options, {})

    return template.render(
        title=metadata.get("title", path.stem),
        navbar=navbar_generator(nav_items_copy),
        skip_header=metadata.get("skip_header", False),
        page_title=page_title,
        page_description=page_description,
        content=rendered_content,
        comment_section=(category == "posts" and not is_directory_index),
        creation_date=metadata.get("creation_date", get_time_now()),
        modified_date=get_last_updated_time(path),
        site_map=site_map,
        current_category=category,
        is_directory_index=is_directory_index
    )


md: MarkdownIt = MarkdownIt()
gfm_like.make()

env: jinja2.Environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates/")
)
template: jinja2.Template = env.get_template("layout.html")

output: Path = Path("out/")
if output.exists() and output.is_dir():
    rmtree(output)
output.mkdir(parents=True, exist_ok=True)
copytree(Path("static/"), output, dirs_exist_ok=True)

nav_items: dict[str, bool] = {
    "main": False,
}
nav_hidden_list = [
    "countdown",
]

for item in Path("pages/").iterdir():
    if not item.is_dir():
        continue
    if item.name in nav_hidden_list:
        continue
    nav_items[item.name] = False

pages_dir: Path = Path('pages/')

site_map: list[dict[str, Any]] = []

# build the site map
for item in pages_dir.rglob('*.md'):
    if not item.is_file():
        continue

    post: frontmatter.Post = frontmatter.load(item)
    rel_path: Path = item.relative_to(pages_dir)
    category: str = rel_path.parts[0] if len(rel_path.parts) > 1 else "main"

    url: str
    if item.name == "index.md":
        url = f"/{rel_path.with_suffix(".html").as_posix()}"
    else:
        url = f"/{rel_path.with_suffix("").as_posix()}/index.html"

    site_map.append({
        "title": post.metadata.get("title", item.stem),
        "creation_date": post.metadata.get(
            "creation_date",
            get_time_now(),
        ),
        # "description": post.metadata.get("description", ""),
        "url": url,
        "category": category,
        "delisted": post.metadata.get("delisted", False),
        "is_index": post.metadata.get("is_directory_index", False)
    })

# sort by date
site_map.sort(
    key=lambda x: parse_strftime(x["creation_date"]),
    reverse=True
)

# parse and render
for item in pages_dir.rglob('*.md'):
    if not item.is_file():
        continue

    post: frontmatter.Post = frontmatter.load(item)

    parsed: str = parse_writeup(
        md,
        nav_items,
        item,
        post.content,
        post.metadata,
        site_map,
        nav_hidden_list
    )
    generated: Path
    if item.name == "index.md":
        generated = output / item.relative_to(pages_dir).with_suffix(".html")
    else:
        generated_parent: Path = output / item.relative_to(pages_dir).with_suffix("")
        generated = generated_parent / Path("index.html")

    generated.parent.mkdir(parents=True, exist_ok=True)

    with open(generated, "w", encoding="utf-8") as out_file:
        out_file.write(parsed)
