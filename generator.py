import datetime
import subprocess
from shutil import copytree, rmtree
from pathlib import Path
from typing import Any

import frontmatter
import html
from markdown_it.presets import gfm_like
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.footnote import footnote_plugin
import jinja2

TIME_FORMAT = "%d %b %Y %H:%M"


def create_media_renderer(md_instance):
    def media_renderer(tokens, idx, options, env):
        token = tokens[idx]
        src = token.attrGet("src") or ""
        alt_raw = token.content or ""
        title_raw = token.attrGet("title")

        alt_escaped = html.escape(alt_raw)
        title_attr = "" if not alt_raw else f' title="{alt_escaped}"'
        caption_text = title_raw if title_raw else alt_raw

        clean_src = src.split('?')[0].lower()
        is_video = clean_src.endswith(('.mp4', '.webm', '.ogv', '.mov'))
        is_audio = clean_src.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac'))

        if is_video:
            if not alt_raw.strip():
                return f'<video controls src="{src}"></video>'
            return (
                f'<figure>\n'
                f'  <video controls src="{src}">{alt_escaped}</video>\n'
                f'  <figcaption>{md_instance.renderInline(caption_text)}</figcaption>\n'
                f'</figure>'
            )

        if is_audio:
            if not alt_raw.strip():
                return f'<audio controls src="{src}"></audio>'
            return (
                f'<figure>\n'
                f'  <audio controls src="{src}">{alt_escaped}</audio>\n'
                f'  <figcaption>{md_instance.renderInline(caption_text)}</figcaption>\n'
                f'</figure>'
            )

        # it's an image at this point
        if not alt_raw.strip():
            return f'<img src="{src}">\n'
        return (
            f'<figure>\n'
            f'  <img src="{src}" alt="{alt_escaped}"{title_attr}>\n'
            f'  <figcaption>{md_instance.renderInline(caption_text)}</figcaption>\n'
            f'</figure>'
        )

    return media_renderer


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
            ["git", "log", "-1", "--format=%cI", "--", str(file_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        date_str: str = result.stdout.strip()

        if date_str:
            return datetime.datetime.fromisoformat(date_str).strftime(TIME_FORMAT)

    except subprocess.CalledProcessError:
        pass

    return get_time_now()


def navbar_generator(nav_items: dict[str, bool]) -> str:
    out: str = ""

    for nav, is_active in nav_items.items():
        line_str: str = ""
        if is_active:
            line_str = f"<span>{nav}</span>"
        else:
            href: str = "/index.html" if nav == "main" else f"/{nav}/index.html"
            line_str = f'<a href="{href}">{nav}</a>'

        out += line_str + "\n"

    return out


def get_url(rel_path: Path) -> str:
    url: str
    if rel_path.name == "index.md":
        url = f"/{rel_path.with_suffix(".html").as_posix()}"
    else:
        url = f"/{rel_path.with_suffix("").as_posix()}/index.html"

    return url


def parse_writeup(
    md: MarkdownIt,
    nav_items: dict[str, bool],
    path: Path,
    content: str,
    metadata: dict,
    site_map: list[dict[str, Any]],
    hidden_nav: list[str],
) -> str:
    rendered_content: str = ""
    page_title = metadata.get("title", path.stem)
    raw_description = metadata.get("description", "")

    rel_path: Path = path.relative_to("pages/")
    category: str = rel_path.parts[0] if len(rel_path.parts) > 1 else "main"

    url = get_url(rel_path)

    is_directory_index: bool = metadata.get("is_directory_index", False)
    nav_items_copy: dict[str, bool] = nav_items.copy()
    if category == "main" or is_directory_index or category in hidden_nav:
        nav_items_copy[category] = True

    if metadata.get("skip_md", False):
        rendered_content = content
    else:
        rendered_content = md.render(content)

    return template.render(
        title=page_title,
        raw_description=raw_description,
        description=md.renderInline(raw_description),
        creation_date=metadata.get("creation_date", get_time_now()),
        show_creation_date=metadata.get("show_creation_date", True),
        modified_date=get_last_updated_time(path),
        article=metadata.get("article", True),
        url=url,
        skip_header=metadata.get("skip_header", False),
        is_directory_index=is_directory_index,
        navbar=navbar_generator(nav_items_copy),
        content=rendered_content,
        comment_section=(category == "posts" and not is_directory_index),
        site_map=site_map,
        current_category=category,
    )


md: MarkdownIt = MarkdownIt()
md.enable("table")
md.use(anchors_plugin, min_level=1, max_level=6)
md.use(tasklists_plugin)
md.use(footnote_plugin)
gfm_like.make()
md.renderer.rules["image"] = create_media_renderer(md)

env: jinja2.Environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates/")
)
template: jinja2.Template = env.get_template("layout.html")

output: Path = Path("out/")
if output.exists() and output.is_dir():
    rmtree(output)
output.mkdir(parents=True, exist_ok=True)
copytree(Path("static/"), output, dirs_exist_ok=True)

NAV_ITEMS: dict[str, bool] = {
    "main": False,
}
NAV_HIDDEN_LIST = ("countdown",)

for item in Path("pages/").iterdir():
    if not item.is_dir():
        continue
    if item.name in NAV_HIDDEN_LIST:
        continue
    NAV_ITEMS[item.name] = False

pages_dir: Path = Path("pages/")

site_map: list[dict[str, Any]] = []

# build the site map
for item in pages_dir.rglob("*.md"):
    if not item.is_file():
        continue

    post: frontmatter.Post = frontmatter.load(item)
    rel_path: Path = item.relative_to(pages_dir)
    category: str = rel_path.parts[0] if len(rel_path.parts) > 1 else "main"

    url = get_url(rel_path)

    site_map.append(
        {
            "title": post.metadata.get("title", item.stem),
            "creation_date": post.metadata.get(
                "creation_date",
                get_time_now(),
            ),
            "description": post.metadata.get("description", ""),
            "url": url,
            "category": category,
            "delisted": post.metadata.get("delisted", False),
            "is_index": post.metadata.get("is_directory_index", False),
        }
    )

# sort by date
site_map.sort(key=lambda x: parse_strftime(x["creation_date"]), reverse=True)

# parse and render
for item in pages_dir.rglob("*.md"):
    if not item.is_file():
        continue

    post: frontmatter.Post = frontmatter.load(item)

    parsed: str = parse_writeup(
        md, NAV_ITEMS, item, post.content, post.metadata, site_map, NAV_HIDDEN_LIST
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
