const fs = require("fs");

// helpers
const edgeKeys = {
  TOP: "top",
  BOTTOM: "bottom",
  LEFT: "left",
  RIGHT: "right",
};
const flipX = (data) => {
  let ret = data;
  return ret.reverse();
};
const flipY = (data) => {
  return data.reduce((result, curVal) => {
    return (result || []).concat([curVal.reverse()]);
  }, []);
};
const rotate = (data) => {
  let ret = data[0].map((val, index) =>
    data.map((row) => row[index]).reverse()
  );
  return ret;
};
const encode = (data) => {
  let checksum = 0,
    idx = 0;
  for (const d of data.reverse()) {
    checksum += d << idx;
    idx += 1;
  }
  return checksum;
};
// defines a Tile
class Tile {
  constructor(tileId, data) {
    this.tileId = tileId;
    this.data = data;
    this.binaryData = [];
    this.encodedOrientations = [];
    this.taken = false;
    this.tranform();
  }

  encodeEdges(data) {
    if (data.length === 0) {
      return;
    }

    let top = [],
      bottom = [],
      right = [],
      left = [],
      n = data.length;

    for (const x in data) {
      top.push(data[0][x]);
      bottom.push(data[n - 1][x]);
      right.push(data[x][n - 1]);
      left.push(data[x][0]);
    }
    // return {
    //   top: encode(top),
    //   bottom: encode(bottom),
    //   left: encode(left),
    //   right: encode(right),
    // };
    return {
      top: top,
      bottom: bottom,
      left: left,
      right: right,
    };
  }
  canMatchEdge(secondTile) {
    const matchingOrientations = secondTile.encodedOrientations;
    for (const o1 of this.encodedOrientations) {
      for (const o2 of matchingOrientations) {
        if (o1["top"] === o2["bottom"]) {
          return edgeKeys.BOTTOM;
        } else if (o1["left"] === o2["right"]) {
          return edgeKeys.RIGHT;
        } else if (o1["right"] === o2["left"]) {
          return edgeKeys.LEFT;
        } else if (o1["bottom"] === o2["top"]) {
          return edgeKeys.TOP;
        }
      }
    }
    return null;
  }
  tranform() {
    //console.log(this.data);
    for (const r in this.data) {
      let cols = [];
      for (const c in this.data) {
        if (this.data[r][c] == "#") {
          cols.push("1");
        } else {
          cols.push("0");
        }
      }
      this.binaryData.push(cols);
    }
    // copy the original data
    //this.encodedOrientations.push(this.encodeEdges(this.binaryData));

    let idx = 4;
    let temp = this.binaryData;
    while (idx > 0) {
      idx -= 1;
      let t = rotate(temp);
      temp = t;
      this.encodedOrientations.push(this.encodeEdges(t));
    }

    // flip along X AXIS
    let flippedY = flipY(this.binaryData);
    idx = 4;
    while (idx > 0) {
      idx -= 1;
      let t = rotate(flippedY);
      flippedY = t;
      this.encodedOrientations.push(this.encodeEdges(t));
    }
  }
}

class Board {
  constructor(tiles) {
    this.tilesData = tiles;
  }

  search() {
    // search for a pair
    let ret = [],
      ans = 1;

    const tiles = Object.values(this.tilesData);
    for (const firstTile of tiles) {
      let corners = [],
        matches = 0;
      for (const secondTile of tiles) {
        if (
          firstTile.tileId != secondTile.tileId &&
          firstTile.taken === false
        ) {
          const mathchingCorner = firstTile.canMatchEdge(secondTile);
          if (mathchingCorner !== null) {
            matches += 1;
            corners.push({
              corner: mathchingCorner,
              tileId: secondTile.tileId,
            });
          }
        }
      }
      if (matches == 2) {
        firstTile.taken = true;
        ans *= parseInt(firstTile.tileId);
        ret.push({
          [firstTile.tileId]: corners,
        });
      }
    }
    return [ret, ans];
  }
}

const readInput = () => {
  const data = fs.readFileSync("./day_20.in", "utf-8");
  const lines = data.split("\n\n");
  let tilesPair = {};
  lines.map((line) => {
    let tileId,
      gridLines = [];
    let lineParts = line.split("\n");
    tileId = lineParts[0].split(" ")[1].split(":")[0];
    lineParts.slice(1).map((linePart) => {
      gridLines.push(linePart);
    });
    tile = new Tile(tileId, gridLines);
    tilesPair[`${tileId}`] = tile;
    //console.log(tileId);
    //console.log(lineParts.slice(1));
  });
  return tilesPair;
};

const sample = () => {
  let sample = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
  ];
  //rotate(sample);
  //flipX(sample);
  y = flipY(sample);
  console.log(y);
};

const solve = () => {
  let tiles = readInput();
  console.log(tiles);
  let board = new Board(tiles);
  const ret = board.search();
  console.log(ret[0]);
  console.log(ret[1]);
};

solve();
//sample();
