//var data = "";
var f_ctx;
var p_ctx;

var field_img;
var field_canvas;

var points_canvas;
var pixel_meters;

const default_data = {path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}]}

var parsed_data  = [default_data]; //stores all the data got from python 

var appData;

var clicked_graph = true;

var data_version = 0; //stores current data version
var new_solve    = true; //whether there is data or not

var robot_width  = 0.6 //Meters 
var robot_height = 0.8 //Meters

const POINT_SIZE = 5;
const PATH_SIZE  = 1;

const real_field_width  = 16; //Meters
const real_field_height = 8; //Meters

class Point {
  constructor(elem) {
    this.color = "rgba(255,255,255, 0.5)";
    this.data = {};  
    this.size = POINT_SIZE;
    this.element = elem; 
    this.getDataFromElement();
  }

  draw(px2m) {
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
    this.data["heading"] = Number(this.element.querySelectorAll('.heading > input')[0].value)*Math.PI/180;
    this.data["switch"] = String(this.element.querySelectorAll('.switch > label > input')[0].checked);
  }
}

class Points {
  constructor () {
    this.points = [];
    this.amount = 0;
    this.update();
  }

  update () {
    this.points = [];
    let points_elements = document.getElementsByClassName("point");
    for (var i = 0; i < points_elements.length; i++) {
      this.points.push(new Point(points_elements[i]));
    }
    this.amount = points_elements.length;

    this.add_handlers();
  }

  getData () {
    this.update();
    let points = [];
    for (var i = 0; i < this.amount; i++) {
      points.push(this.points[i].data);
    } 
    return (points);
  }

  getPointByElement (elem) {
    for (var i = 0; i < this.amount; i++) {
      if (this.points[i].element == elem) {
        return this.points[i]
      }
    }
    return null
  }

  add_handlers () {
    for (var i = 0; i < this.amount; i++)  {
      this.points[i].element.addEventListener('mousemove', function () {point_hover(this, true);} );
      this.points[i].element.addEventListener('click', function () {point_hover(this, true);} );
      this.points[i].element.addEventListener('mouseout' , function () {point_hover(this, false);} );
    }
  }

  draw () {
    p_ctx.shadowColor = '#101010';
    p_ctx.shadowBlur = 10;

    p_ctx.clearRect(0, 0, points_canvas.width, points_canvas.height);

    for (var i = 0; i < this.amount; i++){
      this.points[i].draw(pixel_meters);
    }
  }
}

class Params {
  constructor () {
    this.params = {};
    this.update();
  }

  update () {
    this.params["poly"] = Number(document.getElementById("polynom").value);
    this.params["pos"] = Number(document.getElementById("position").value);
    this.params["angle"] = Number(document.getElementById("angle").value);
    this.params["radius"] = Number(document.getElementById("radius").value);
    this.params["radius_cont"] = Number(document.getElementById("radius_cont").value);
    this.params["length"] = Number(document.getElementById("length").value);
    this.params["method"] = document.getElementById("method").checked;
  }

  load (path_data) {
    document.getElementById("polynom").value = this.params["poly"]; 
    document.getElementById("position").value = this.params["pos"]; 
    document.getElementById("angle").value = this.params["angle"]; 
    document.getElementById("radius").value = this.params["radius"]; 
    document.getElementById("radius_cont").value = this.params["radius_cont"];
    document.getElementById("length").value = this.params["length"]; 
    document.getElementById("method").checked = this.params["method"]; 
    
    if (path_data[0]["costs"] != null) {
    document.getElementById("pos_cost_val").innerHTML = path_data[0]["costs"]["pos_cost"].toPrecision(3);
    document.getElementById("angle_cost_val").innerHTML = path_data[0]["costs"]["angle_cost"].toPrecision(3);
    document.getElementById("radius_cost_val").innerHTML = path_data[0]["costs"]["radius_cost"].toPrecision(3);
    document.getElementById("radius_cont_cost_val").innerHTML = path_data[0]["costs"]["radius_cont_cost"].toPrecision(3);
    document.getElementById("length_cost_val").innerHTML = path_data[0]["costs"]["length_cost"].toPrecision(3);
    }
  }

  getData () {
    return(this.params);
  }
}

class AppData {
  constructor() {   
    this.version = 0;
    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData = [defaultData];
  }

  updateForms () {
    this.solverData[this.version]["params"].load(this.solverData[this.version]["path"])    
  }

  newVersion (push_item) {
    if (this.version < this.solverData.length) {
      this.solverData.splice(this.version+1, this.solverData.length);
    }

    let defaultData = {
      path: [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}],
      traj: {},
      points: new Points(),
      params: new Params()};

    this.solverData.push(defaultData);
    this.version++;

    this.solverData[this.version]["path"] = push_item["path"];
    this.solverData[this.version]["traj"] = push_item["traj"];

    this.updateForms();
  }

  reset () {
    this.version = 0;
    this.updateForms();
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
    this.solverData[this.version]["params"].update();
    return(this.solverData[this.version]["params"]);
  }
  getPoints () {
    this.solverData[this.version]["points"].update();
    return(this.solverData[this.version]["points"]);
  }
  getPath () {
    return(this.solverData[this.version]["path"]);
  }
  getTraj () {
    return(this.solverData[this.version]["traj"]); 
  }
  loadData (prevData) {
    //this = prevData;
  }
}

function point_hover (elem, hover) {
  point = appData.getPoints().getPointByElement(elem);
  if (hover) {
    point.size = POINT_SIZE*1.2;
    point.color = "rgba(255,255,255, 0.9)";
  }
  else {
    point.size = POINT_SIZE;
    point.color = "rgba(255,255,255, 0.5)";
  }

  appData.getPoints().draw();
}

function get_mouse_pos (canvas, evt) {
  var rect = canvas.getBoundingClientRect();
  return {x: evt.clientX - rect.left, y: evt.clientY - rect.top};
}

function draw_path (path_points){
  f_ctx.beginPath();
  
  var inc = 2; 
  for (var i = 0; i < path_points.length - inc; i+=inc){
    var val = parseInt(i*100/path_points.length);
    color = "#bbbbbb";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();
    
    let x = path_points[i]["x"];
    let y = path_points[i]["y"];
    let x1 = path_points[i+inc]["x"];
    let y1 = path_points[i+inc]["y"];

    let alpha = Math.atan2((y1-y),(x1-x));
    
    x = x + Math.cos(alpha)*robot_height/2;
    y = y + Math.sin(alpha)*robot_height/2;

    let xr = Math.cos(alpha+Math.PI/2)*robot_width/2 + x;
    let yr = Math.sin(alpha+Math.PI/2)*robot_width/2 + y;
    
    let xl = Math.cos(alpha-Math.PI/2)*robot_width/2 + x;
    let yl = Math.sin(alpha-Math.PI/2)*robot_width/2 + y;

    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
    
    color = "#666666";
    f_ctx.fillStyle = color;

    x = path_points[i]["x"];
    y = path_points[i]["y"];
    
    x = x + Math.cos(alpha+Math.PI)*robot_height/2;
    y = y + Math.sin(alpha+Math.PI)*robot_height/2;

    xr = Math.cos(alpha+Math.PI/2)*robot_width/2 + x;
    yr = Math.sin(alpha+Math.PI/2)*robot_width/2 + y;
    
    xl = Math.cos(alpha-Math.PI/2)*robot_width/2 + x;
    yl = Math.sin(alpha-Math.PI/2)*robot_width/2 + y;

    f_ctx.beginPath();
    f_ctx.arc (xr*pixel_meters, yr*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.arc (xl*pixel_meters, yl*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  for (var i = 0; i < path_points.length; i+=inc){
    var val = parseInt(i*100/path_points.length);
    color = "hsl("+val+",100%,60%)";
    f_ctx.fillStyle = color;
    f_ctx.beginPath();
    f_ctx.arc (path_points[i]["x"]*pixel_meters, path_points[i]["y"]*pixel_meters, PATH_SIZE, 0, 2*Math.PI);
    f_ctx.fill();
  }

  f_ctx.closePath();
}

function init_field() {
  $("#loader").hide();
  //$("#params_cont").blur();
  field_canvas = document.getElementById("field_canvas");
  points_canvas = document.getElementById("points_canvas");

  f_ctx = field_canvas.getContext('2d');
  p_ctx = points_canvas.getContext('2d');
  
  field_img = new Image;

  appData = new AppData();

  field_img.onload = function() {
    f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    appData.getPoints().draw();
  };

  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
}

function draw_field() {
    f_ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    f_ctx.shadowBlur = 0;

    for (var i = 0; i < appData.getPath().length; i++) {
      draw_path(appData.getPath()[i]["path_points"]);
    }
    
    document.getElementById("version-header").innerHTML = data_version + " / " + (parsed_data.length-1)
    
    f_ctx.shadowBlur = 10;
    appData.getPoints().draw();

    update_forms();
}

function update_forms () {
  if (Number(document.getElementById("polynom").value) != 5) {
      document.getElementById("method").disabled = true;
      document.getElementById("method").checked = false;
    }
    else {
      document.getElementById("method").disabled = false; 
    }
}

//delete future changes and push new version of paths
function new_version (push_item) {
  appData.newVersion(push_item);
  clicked_graph = false;
  show_graph();
  
  let path_dur = appData.getTraj()["time"][appData.getTraj()["time"].length-1].toPrecision(3);
  document.getElementById('time-header').innerHTML =  "Duration: " + path_dur + " s";
  
  draw_field();
}

function reset_data () {
  appData.reset();
  appData.getPoints().update();
  new_solve = true;
  $("#download").hide(300);
  $(".traj-area").hide(200)
  clicked_graph = true;
  draw_field();
}

function redo_change () {
  appData.redo();
  draw_field();
}

function undo_change () {
  appData.undo();
  draw_field();
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' step='0.1' placeholder='X' oninput='reset_data()' value="+
    //Math.min(real_field_width,(points.getData()[points.amount-1]["x"]+1))+
    1 +
    "></td>" +
    "<td class='y'><input class='form-control form-control-small' type='number' step='0.1' placeholder='Y' oninput='reset_data()' value="+
    //Math.min(real_field_height,(points.getData()[points.amount-1]["y"]+1))+
    1 + 
    "></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='reset_data()' value=0></td>"+
    "<td class='switch'><label class='toggle'><input type='checkbox' onclick='reset_data()' value='true'><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
  
  reset_data();
}

function delete_point (elem) {
  if (appData.getPoints().amount > 1) {
    $(elem).parent().parent().remove();
    reset_data();
  }
}

function solve() {
  let points_data = appData.getPoints().getData();
  let params = appData.getParams().getData();

  var data=[];
  var start = 0;
  var path_num = 0;

  for(var i = 0; i < points_data.length; i++)  {
    if (i == points_data.length - 1) {
      data.push({
        "params": params, 
        "points":points_data.slice(start),
        "scalars_x":appData.getPath()[path_num]["scalars_x"], 
        "scalars_y":appData.getPath()[path_num]["scalars_y"]});
      }

    if (points_data[i]["switch"]  == "true") {   
      data.push({
        "params": params, 
        "points":points_data.slice(start, i + 1),
        "scalars_x":appData.getPath()[path_num]["scalars_x"], 
        "scalars_y":appData.getPath()[path_num]["scalars_y"]});
      start = i;
    
      if (!new_solve) {
        path_num++;
      }  
    }
  }

  //$("#params_cont").blur();
  $("#download").hide(300);
  $("#loader").show(300);

  var data = JSON.stringify(data);
  
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status) {
    $("#loader").hide(300);
    //$("#params_cont").unblur();
    $("#download").show(300);
    new_solve = false;
    new_version(JSON.parse(data));
  });
}
