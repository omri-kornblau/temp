const fs = require('fs');
const {dialog} = require('electron').remote;
const path = require('path');

// Drawing canvases
let f_ctx;
let p_ctx;
let field_img;
let field_canvas;
let points_canvas;
let pixel_meters;

// Points drawing sizes
const POINT_SIZE = 5;
const PATH_SIZE  = 1;

// Field size constants
const realFieldWidth  = 16.46; // meters
const realFieldHeight = 8.23; // meters

// Zoom and pan
let zoomAmount = 1;

let panTrackX = 0;
let panTrackY = 0;

let panActive = false;
let mousePressed = false;
let prevMouseX = 0;
let prevMouseY = 0;

// Store all paths data and parameters
let appData;

const default_data = {path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}]}

let clickedGraph = true;

let data_version = 0; //stores current data version
let newSolve    = true; //whether there is data or not

function toPrec (inp ,prec) {
  ans = inp*Math.pow(10, prec);
  ans = Math.round(ans, 0)/Math.pow(10, prec);
  return(String(ans));
}

function putAngleInRange (angle, flipDirection=true) {
  if (flipDirection) {
    angle *= -1;
  }

  while (angle >= Math.PI) {
    angle -= 2 * Math.PI;
  }

  while (angle < 0) {
    angle += 2 * Math.PI;
  }
  return (angle);
}

class Point {
  constructor(elem) {
    this.color = "rgba(255,255,255, 0.5)";
    this.directionColor = "rgba(255,255,255, 0.5)";
    this.headingColor = "rgba(255,50,50, 0.5)";
    this.data = {};
    this.size = POINT_SIZE;
    this.element = elem;
    this.getDataFromElement();
  }

  draw(px2m) {
    let angle, armLen;
    p_ctx.beginPath();
    angle = this.data["direction"];
    armLen = 20;
    p_ctx.strokeStyle = this.directionColor;
    p_ctx.moveTo(this.data["x"]*px2m+Math.cos(angle)*this.size, this.data["y"]*px2m+Math.sin(angle)*this.size);
    p_ctx.lineTo(this.data["x"]*px2m+Math.cos(angle)*armLen, this.data["y"]*px2m+Math.sin(angle)*armLen);
    p_ctx.lineCap = 'round';
    p_ctx.lineWidth = 4;
    p_ctx.stroke();
    p_ctx.beginPath();
    angle = this.data["heading"];
    armLen = 15;
    p_ctx.strokeStyle = this.headingColor;
    p_ctx.moveTo(this.data["x"]*px2m+Math.cos(angle)*this.size, this.data["y"]*px2m+Math.sin(angle)*this.size);
    p_ctx.lineTo(this.data["x"]*px2m+Math.cos(angle)*armLen, this.data["y"]*px2m+Math.sin(angle)*armLen);
    p_ctx.lineCap = 'round';
    p_ctx.lineWidth = 3;
    p_ctx.stroke();
    p_ctx.beginPath();
    p_ctx.arc (this.data["x"]*px2m, this.data["y"]*px2m, this.size, 0, 2*Math.PI);
    p_ctx.fillStyle = this.color;
    p_ctx.fill();
  }

  distance(point_x, point_y) {
    return Math.sqrt((this.data["x"]-point_x)^2+(this.data["y"]-point_y)^2);
  }

  getDataFromElement () {
    this.data["x"] = Number(this.element.querySelectorAll('.x > input')[0].value);
    this.data["y"] = Number(this.element.querySelectorAll('.y > input')[0].value);
    this.data["direction"] = Number(this.element.querySelectorAll('.direction > input')[0].value)*Math.PI/180;
    this.data["heading"] = Number(this.element.querySelectorAll('.heading > input')[0].value)*Math.PI/180;
    this.data["start_mag"] = Number(this.element.querySelectorAll('.start_mag > input')[0].value);
    this.data["end_mag"] = Number(this.element.querySelectorAll('.end_mag > input')[0].value);
    this.data["slow_dist"] = Number(this.element.querySelectorAll('.slow_dist > input')[0].value);
    this.data["stop"] = String(this.element.querySelectorAll('.stop > .stop-checkbox')[0].classList.contains('checked'));
  }
}

class Points {
  constructor () {
    this.points = [];
    this.amount = 0;
    this.update();
    this.solvePoints = this.points;
  }

  update () {
    this.points = [];
    let points_elements = document.getElementsByClassName("point");
    for (let i = 0; i < points_elements.length; i++) {
      this.points.push(new Point(points_elements[i]));
    }
    this.amount = points_elements.length;

    this.add_handlers();
  }

  getData () {
    this.update();
    let points = [];
    for (let i = 0; i < this.amount; i++) {
      points.push(this.points[i].data);
    }
    return (points);
  }

  getPointByElement (elem) {
    for (let i = 0; i < this.amount; i++) {
      if (this.points[i].element == elem) {
        return this.points[i];
      }
    }
    return null;
  }

  add_handlers () {
    for (let i = 0; i < this.amount; i++)  {
      this.points[i].element.addEventListener('mouseenter', function () {pointHover(this, true);} );
      this.points[i].element.addEventListener('click', function () {pointHover(this, true);} );
      this.points[i].element.addEventListener('mouseleave', function () {pointHover(this, false);} );
    }
  }

  draw () {
    p_ctx.shadowColor = '#101010';
    //p_ctx.shadowBlur = 4;

    p_ctx.clearRect(0, 0, points_canvas.width, points_canvas.height);

    for (let i = 0; i < this.amount; i++){
      this.points[i].draw(pixel_meters);
    }
  }

  load () {
    $('#points').html("");
    for (let i = 0; i < this.solvePoints.length; i++) {
      addPoint(this.solvePoints[i].data["x"],
                this.solvePoints[i].data["y"],
                this.solvePoints[i].data["direction"],
                this.solvePoints[i].data["heading"],
                this.solvePoints[i].data["start_mag"],
                this.solvePoints[i].data["end_mag"],
                this.solvePoints[i].data["slow_dist"],
                this.solvePoints[i].data["stop"],
                false);
    }
    this.points = this.solvePoints;
  }

  savePoints () {
    this.solvePoints = this.points;
  }
}

class Params {
  constructor () {
    this.params = {};
    this.update();
  }

  update () {
    let input_elements = document.getElementsByClassName("form-control-param");
    for (let i = 0; i < input_elements.length; i++) {
      this.params[input_elements[i].getAttribute('id')] = Number(input_elements[i].value);
    }
    this.params['method'] = document.getElementById('method').checked;
  }

  load (path_data) {
    let input_elements = document.getElementsByClassName("form-control-param");
    for (let i = 0; i < input_elements.length; i++) {
      //handle cases where there are no costs (e.g. init)
        input_elements[i].value = this.params[input_elements[i].getAttribute('id')];
    }

    if (path_data[0]["costs"] != NaN) {
        document.getElementById("pos_cost_val").innerHTML = path_data[0]["costs"]["pos_cost"].toPrecision(3);
        document.getElementById("angle_cost_val").innerHTML = path_data[0]["costs"]["angle_cost"].toPrecision(3);
        document.getElementById("radius_cost_val").innerHTML = path_data[0]["costs"]["radius_cost"].toPrecision(3);
        document.getElementById("radius_cont_cost_val").innerHTML = path_data[0]["costs"]["radius_cont_cost"].toPrecision(3);
        document.getElementById("length_cost_val").innerHTML = path_data[0]["costs"]["length_cost"].toPrecision(3);
    }

    document.getElementById('method').checked = this.params['method'];
  }

  getData () {
    return(this.params);
  }
}

class AppData {
  constructor() {
    this.version = 0;
    this.name = "untitled";
    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData = [defaultData];
  }

  updateForms () {
    this.solverData[this.version]["params"].load(this.solverData[this.version]["path"]);
    this.solverData[this.version]["points"].load();
    document.getElementById("auto_name").value = this.name;

    drawField(false);
  }

  newVersion () {
    if (this.version < this.solverData.length) {
      this.solverData.splice(this.version+1, this.solverData.length);
    }

    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData.push(defaultData);
    this.version ++;

    this.solverData[this.version]["points"].update();
    this.solverData[this.version]["points"].savePoints();
  }

  saveSolverData (solverData) {
    this.solverData[this.version]["path"] = solverData["path"];
    this.solverData[this.version]["traj"] = solverData["traj"];
    this.solverData[this.version]["params"].load(this.solverData[this.version]["path"]);
  }

  reset () {
    this.solverData[this.version].path.scalars_x = null;
    this.solverData[this.version].path.scalars_y = null;
    this.updateForms() ;
  }

  undo () {
    if (this.version > 1) {
      this.version --;
      this.updateForms();
    }
  }

  redo () {
    if (this.version < this.solverData.length -1) {
      this.version ++;
      this.updateForms();
    }
  }

  getParams () {
    return(this.solverData[this.version]["params"]);
  }
  getPoints () {
    return(this.solverData[this.version]["points"]);
  }
  getPath () {
    return(this.solverData[this.version]["path"]);
  }
  getTraj () {
    return(this.solverData[this.version]["traj"]);
  }

  createTrajFile (precision=3) {
    const seperator = "\t";
    let output = "";

    for (let path of this.getPath()) {
      const traj = path.traj;
      const maxTime = traj["time"][traj["time"].length-1];

      for (let i = 0; i < traj["time"].length; i++) {
        output += toPrec((maxTime - traj["time"][i]), precision) + seperator;
        // Inevrted x and y for 1690s robot
        output += toPrec(-1*traj["y"][i] + realFieldHeight/2, precision) + seperator;
        output += toPrec(traj["x"][i], precision) + seperator;
        output += toPrec(-1*traj["vy"][i], precision) + seperator;
        output += toPrec(traj["vx"][i], precision) + seperator;
        output += toPrec(putAngleInRange(traj["heading"][i]), precision) + seperator;
        output += toPrec(-1 * traj["wheading"][i], precision) + seperator;
        output += (traj["slow"][i] ? "1" : "0") + seperator;
        output += "\n";
      }
    }

    return output;
  }

  createAppDataFile () {
    let pointsData = [];
    this.getPoints().points.forEach(point => {
      pointsData.push(point.data);
    });

    let dataObject = {
      name: this.name,
      params: this.getParams(),
      points: pointsData,
      path: this.getPath(),
      traj: this.getTraj()
    }

    return JSON.stringify(dataObject);
  }

  loadData (data) {
    this.name = data.name;
    this.solverData[this.version].params.params = data.params.params;
    this.solverData[this.version].path = data.path;
    this.solverData[this.version].traj = data.traj;

    $('#points').html("");

    data.points.forEach(point => {
      addPoint(
        point["x"],
        point["y"],
        point["direction"],
        point["heading"],
        point["start_mag"],
        point["end_mag"],
        point["slow_dist"],
        point["stop"],
        false);
    });

    // this.getPoints().update();
    // this.solverData[this.version].points.solvePoints = this.solverData[this.version].points.points;
    // this.updateForms();
    // this.getPoints().update();
  }
}

function pointHover (elem, hover) {
  point = appData.getPoints().getPointByElement(elem);
  if (hover) {
    point.size = POINT_SIZE*1.3;
    point.color = "rgba(255,255,255, 0.9)";
    point.directionColor = "rgba(255,255,255, 0.9)";
    point.headingColor = "rgba(255,50,50, 0.9)";
  }
  else {
    point.size = POINT_SIZE;
    point.color = "rgba(255,255,255, 0.5)";
    point.directionColor = "rgba(255,255,255, 0.5)";
    point.headingColor = "rgba(255,50,50, 0.5)";
  }

  appData.getPoints().draw();
}

function get_mouse_pos (canvas, evt) {
  let rect = canvas.getBoundingClientRect();
  return {x: evt.clientX - rect.left, y: evt.clientY - rect.top};
}

function drawPath (path){
  path_points = path.path_points;

  let robotWidth = appData.getParams().params["width"];
  let robotHeight = appData.getParams().params["height"];
  f_ctx.beginPath();
  let inc = 2;
  for (let i = 0; i < path_points.length - inc; i+=inc){
    let val = parseInt(i*100/path_points.length);
    color = "#bbbbbb";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();

    let x = path_points[i]["x"];
    let y = path_points[i]["y"];
    let x1 = path_points[i+inc]["x"];
    let y1 = path_points[i+inc]["y"];

    let traj_i = parseInt(i*path.traj.heading.length/path_points.length);
    let heading = path.traj.heading[traj_i];
    let alpha = heading;

    x = x + Math.cos(alpha)*robotHeight/2;
    y = y + Math.sin(alpha)*robotHeight/2;

    let xr = Math.cos(alpha+Math.PI/2)*robotWidth/2 + x;
    let yr = Math.sin(alpha+Math.PI/2)*robotWidth/2 + y;

    let xl = Math.cos(alpha-Math.PI/2)*robotWidth/2 + x;
    let yl = Math.sin(alpha-Math.PI/2)*robotWidth/2 + y;

    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();

    color = "#666666";
    f_ctx.fillStyle = color;

    x = path_points[i]["x"];
    y = path_points[i]["y"];

    x = x + Math.cos(alpha+Math.PI)*robotHeight/2;
    y = y + Math.sin(alpha+Math.PI)*robotHeight/2;

    xr = Math.cos(alpha+Math.PI/2)*robotWidth/2 + x;
    yr = Math.sin(alpha+Math.PI/2)*robotWidth/2 + y;

    xl = Math.cos(alpha-Math.PI/2)*robotWidth/2 + x;
    yl = Math.sin(alpha-Math.PI/2)*robotWidth/2 + y;

    f_ctx.beginPath();
    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  for (let i = 0; i < path_points.length; i+=inc){
    let traj_i = parseInt(i*path.traj.vel.length/path_points.length);
    let vel_hue = Math.abs(path.traj.vel[traj_i])
    vel_hue = 100-parseInt(vel_hue*100/appData.getParams().getData()["max_vel"]);
    color = "hsl("+vel_hue+",100%,60%)";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();
    f_ctx.arc (path_points[i].x*pixel_meters, path_points[i].y*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  f_ctx.closePath();
}

function initField() {
  $("#loader").hide();
  //$("#params_cont").blur();
  field_canvas = document.getElementById("field_canvas");
  points_canvas = document.getElementById("points_canvas");

  f_ctx = field_canvas.getContext('2d');
  p_ctx = points_canvas.getContext('2d');

  f_ctx.transform(1, 0, 0, -1, 0, field_canvas.height)
  p_ctx.transform(1, 0, 0, -1, 0, field_canvas.height)

  points_canvas.addEventListener('mousedown', (event) => {
    if (panActive) {
      prevMouseX = event.x;
      prevMouseY = event.y;
      mousePressed = true;
    }
  }, false);

  points_canvas.addEventListener('mouseup', (event) => {
    if (panActive) {
      mousePressed = false;
    }
  }, false);

  points_canvas.addEventListener('mousemove', (event) => {
    if (panActive && mousePressed) {
      let diffX = -(prevMouseX - event.x);
      let diffY = (prevMouseY - event.y);

      let isInCanvas =
        (Math.abs(panTrackX-diffX) <= (realFieldWidth*zoomAmount - realFieldWidth)*pixel_meters)
        && (Math.abs(panTrackY+diffY) <= (realFieldHeight*zoomAmount - realFieldHeight)*pixel_meters);

      if ((zoomAmount > 1) && isInCanvas) {

        panTrackX += diffX;
        panTrackY += diffY;

        p_ctx.transform(1, 0, 0, 1, diffX, diffY);
        f_ctx.transform(1, 0, 0, 1, diffX, diffY);

        drawField();

      }

      prevMouseX = event.x;
      prevMouseY = event.y;
    }
  }, false);

  field_img = new Image;

  appData = new AppData();

  field_img.onload = function() {
    f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    appData.getPoints().draw();
  };

  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/realFieldWidth;
}

function drawField(cleanPath=false) {
  f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
  if (!newSolve) {
    //f_ctx.shadowBlur = 0; shadows will make render slower
      if(!cleanPath) {
        for (let i = 0; i < appData.getPath().length; i++) {
          drawPath(appData.getPath()[i]);
        }
      }
    }
    document.getElementById("version-header").innerHTML = appData.version + " / " + (appData.solverData.length-1)

    //f_ctx.shadowBlur = 10;
    appData.getPoints().draw();

    updateForms();
}

function updateForms () {
  if (Number(document.getElementById("poly").value) != 5) {
      document.getElementById("method").disabled = true;
      document.getElementById("method").checked = false;
    }
    else {
      document.getElementById("method").disabled = false;
    }
}

//delete future changes and push new version of paths
function newVersion() {
  clickedGraph = false;

  showGraph();

  setDuration("Duration: ");

  drawField();
}

function reset(cleanPath=true) {
  appData.getPoints().update();
  newSolve = true;
  clickedGraph = true;
  if (newSolve) {
    $("#download").hide(300);
    $(".traj-area").hide(200);
  }
  drawField(cleanPath);
}

function change () {
  appData.getPoints().update();
  setDuration("Duration: ");
  clickedGraph = true;
  newSolve = false;
  drawField(false);
  $("#download").show(100);
}

function resetData () {
  appData.reset();
  change();
}

function redo_change () {
  appData.redo();
  change();
}

function undo_change () {
  appData.undo();
  change();
}

function addPoint (x=-1, y=-1, direction=0, heading=0, start_mag=1, end_mag=1, slow=0, reverse=false, draw=true) {
  if (x < 0) {
    x = Math.min(realFieldWidth,(appData.getPoints().getData()[appData.getPoints().amount-1]["x"]+1));
    y = Math.min(realFieldWidth,(appData.getPoints().getData()[appData.getPoints().amount-1]["y"]+1));
  }
  $('#points').append(`<tr class="point move-cursor">`+
    `<td class="delete"><a class="btn btn-link btn-small" onclick="alignRobot(this)">` +
    `<i class="glyphicon glyphicon-object-align-left glyphicon-small"></i>` +
    `</a></td>` +
    `<td class="x"><input class="form-control form-control-small" type="number" step="0.1" placeholder="X" oninput="reset()" value=` +
    x +
    `></td>` +
    `<td class="y"><input class="form-control form-control-small" type="number" step="0.1" placeholder="Y" oninput="reset()" value=` +
    y +
    `></td>`+
    `<td class="direction"><input class="form-control form-control-small" type="number" placeholder="α" oninput="reset()" step="5" value=`+
    direction*180/Math.PI +
    "></td>"+
    `<td class="heading"><input class="form-control form-control-small" type="number" placeholder="α" oninput="reset()" step="5" value=`+
    heading*180/Math.PI +
    "></td>"+
    `<td class="start_mag"><input class="form-control form-control-small" type="number" placeholder="mag" oninput="reset()" step="0.1" value=` +
    start_mag +
    `></td>` +
    `<td class="end_mag"><input class="form-control form-control-small" type="number" placeholder="mag" oninput="reset()" step="0.1" value=` +
    end_mag +
    `></td>` +
    `<td class="slow_dist"><input class="form-control form-control-small" type="number" placeholder="slow" oninput="reset()" step="0.1" value=` +
    slow +
    `></td>` +
    // `<td class="stop"><label class="toggle" onclick="reset()"><input type="checkbox" ${(reverse === "true" ? "checked" : "")}>`+
    `<td class="stop"><a class="` +
    (reverse === 'true' ? "checked " : "") +
    `stop-checkbox" onclick="toggleCheckBox(this); reset();"><i class="glyphicon glyphicon-retweet"></i></a>` +
    `</td>` +
    `<td class="delete"><a class="btn btn-danger btn-small" onclick="deletePoint(this)">`+
    `<i class="glyphicon glyphicon-trash glyphicon-small"></i>`+
    `</a></td>`+
    `</tr>`);
  if (draw) {
    reset();
  }
}

function deletePoint (elem) {
  if (appData.getPoints().amount > 2) {
    $(elem).parent().parent().remove();
    reset();
  }
}

function alignRobot (elem) {
  let pointElem = elem.parentNode.parentNode;
  appData.getPoints().getPointByElement(pointElem).data["x"] = appData.getParams().getData()["height"]/2;
  pointElem.querySelectorAll('.x > input')[0].value = appData.getParams().getData()["height"]/2;
  appData.getPoints().getPointByElement(pointElem).data["heading"] = 0;
  pointElem.querySelectorAll('.heading > input')[0].value = 0;
}

function saveTraj () {
  let options = {title: "Save Trajectory File", defaultPath: (appData.name)}
  console.log(dialog.showSaveDialog(options,(fileName) => {
    if (fileName === undefined) {
        return;
    }

    fs.writeFile(`${fileName}.txt`, appData.createTrajFile(), (err) => {
      if (err) console.log(err);
    });
  }));
}

function saveAppData () {
  const options = {title: "Save Auto File", defaultPath: (appData.name + ".auto")}
  console.log(dialog.showSaveDialog(options,(fileName) => {
    if (fileName === undefined) {
      return;
    }

    if (!fileName.includes('.auto')) {
      fileName += '.auto';
    }

    fs.writeFile(fileName, appData.createAppDataFile(), (err) => {
      if (err) console.log(err);
    })

    appData.name = path.basename(fileName).split('.auto')[0];
    document.getElementById("auto_name").value = appData.name;
  }));
}

function loadAppData () {
  const options = {properties: ['openFile', 'multiSelections'], defaultPath: (appData.name + ".auto")}
  dialog.showOpenDialog(options, (files) => {
    if (files !== undefined) {
      fs.readFile(files[0], (err, jsonData) => {
        appData = new AppData();

        appData.loadData(JSON.parse(jsonData));

        setDuration("Duration: ");
        clickedGraph = true;
        newSolve = false;
        drawField(false);
        $("#download").show(100);
      });
    }
  });
}

function zoom (amount) {
  if (amount > 0) {
    f_ctx.transform(1, 0, 0, 1, -panTrackX, -panTrackY);
    p_ctx.transform(1, 0, 0, 1, -panTrackX, -panTrackY);

    panTrackX = 0;
    panTrackY = 0;

    if (zoomAmount*amount >= 1) {
      p_ctx.transform(amount, 0, 0, amount, 0, 0);
      f_ctx.transform(amount, 0, 0, amount, 0, 0);
      zoomAmount *= amount;
    }
  }
  else {
    amount = 0.8;

    f_ctx.transform(1, 0, 0, 1, -panTrackX, -panTrackY);
    p_ctx.transform(1, 0, 0, 1, -panTrackX, -panTrackY);

    panTrackX = 0;
    panTrackY = 0;

    while (zoomAmount > 1) {
      p_ctx.transform(amount, 0, 0, amount, 0, 0);
      f_ctx.transform(amount, 0, 0, amount, 0, 0);

      zoomAmount *= amount;
    }
  }
  drawField();
}

function pan () {
  panActive = !panActive;
  if (panActive) {
    points_canvas.style.cursor = "move";
  }
  else {
    points_canvas.style.cursor = "initial";
  }
}

//The function is called to solve things with python
//Command can be 0, 1 or 2 --> path+traj, path, traj
function solve (command=0) {
  appData.getPoints().update();
  appData.getParams().update();

  let pointsData = appData.getPoints().getData();
  let params = appData.getParams().getData();

  let data = [];

  let start = 0;
  let path_num = 0;

  for(let i = 0; i < pointsData.length; i++)  {
    if (i == pointsData.length - 1) {
      data.push({
        "params": params,
        "points":pointsData.slice(start),
        "scalars_x":appData.getPath()[path_num]["scalars_x"],
        "scalars_y":appData.getPath()[path_num]["scalars_y"],
        "slow_end":pointsData[i]["slow_dist"],
        "slow_start":(start === 0) ? pointsData[start]["slow_dist"] : 0
      });
    }

    if (pointsData[i]["stop"]  == "true") {
      if (i !== 0) {
        data.push({
          "params": params,
          "points":pointsData.slice(start, i + 1),
          "scalars_x":appData.getPath()[path_num]["scalars_x"],
          "scalars_y":appData.getPath()[path_num]["scalars_y"],
          "slow_end":pointsData[i]["slow_dist"],
          "slow_start":(start === 0) ? pointsData[start]["slow_dist"] : 0
        });

        start = i + 1;

        if (!newSolve) {
          path_num++;
        }
      }
    }
  }

  appData.newVersion();

  //$("#params_cont").blur();
  $("#download").hide(300);
  $("#loader").show(300);

  let sentData = JSON.stringify({'data': data, 'cmd': command});

  $.post("http://127.0.0.1:3000/", {'data': sentData}, function(data, status) {
    $("#loader").hide(300);
    $("#download").show(300);
    newSolve = false;

    appData.saveSolverData(JSON.parse(data));

    newVersion();
  });
}

function toggleCheckBox (elem) {
  $(elem).toggleClass('checked');
}
