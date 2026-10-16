
import os
import json
import urllib.request
from PIL import Image, ImageDraw

token = os.environ["GH_TOKEN"]
username = os.environ["GH_USERNAME"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            weekday
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": username}
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "growing-snake"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

if "errors" in result:
    raise RuntimeError(result["errors"])

weeks = result["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]["weeks"]

cols = 53
rows = 7
cell = 9
margin = 12
dot = 6

grid = [
    [{"count": 0, "color": "#161b22"} for _ in range(rows)]
    for _ in range(cols)
]

for x, week in enumerate(weeks[:cols]):
    for day in week["contributionDays"]:
        grid[x][day["weekday"]] = {
            "count": day["contributionCount"],
            "color": day["color"]
        }

path = []

for y in range(rows):
    xs = range(cols) if y % 2 == 0 else range(cols - 1, -1, -1)
    for x in xs:
        path.append((x, y))

width = cols * cell + margin * 2
height = rows * cell + margin * 2

background = "#0d1117"
snake_color = "#39ff14"
head_color = "#ffffff"

body = [path[0]]
eaten = set()
frames = []

def make_frame():
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    for x in range(cols):
        for y in range(rows):
            if (x, y) in eaten:
                continue

            px = margin + x * cell
            py = margin + y * cell

            draw.rounded_rectangle(
                (px, py, px + dot, py + dot),
                radius=1,
                fill=grid[x][y]["color"]
            )

    for x, y in body[:-1]:
        px = margin + x * cell
        py = margin + y * cell

        draw.rounded_rectangle(
            (px, py, px + dot, py + dot),
            radius=2,
            fill=snake_color
        )

    x, y = body[-1]
    px = margin + x * cell
    py = margin + y * cell

    draw.rounded_rectangle(
        (px, py, px + dot, py + dot),
        radius=2,
        fill=head_color
    )

    return image

frames.append(make_frame())

for position in path[1:]:
    x, y = position
    body.append(position)

    if grid[x][y]["count"] > 0:
        eaten.add(position)
    else:
        body.pop(0)

    frames.append(make_frame())

os.makedirs("dist", exist_ok=True)

frames = [
    frame.convert("P", palette=Image.Palette.ADAPTIVE)
    for frame in frames
]

frames[0].save(
    "dist/github-snake.gif",
    save_all=True,
    append_images=frames[1:],
    duration=90,
    loop=0,
    optimize=True,
    disposal=2
)

print("Growing snake GIF generated successfully!")
