var data = ""
var ctx;
var field_img;
var field_canvas;
var pixel_meters;

var path_points = [];

const point_size = 5;
const path_size = 3;
const real_field_width = 16; //Meters
const real_field_height = 8; //Meters

function get_points () {
  var points_elements = document.getElementsByClassName("point");
  var points = [];
  for (var i = 0; i < points_elements.length; i++) {
    var point = {};
    point["x"] = Number(points_elements[i].querySelectorAll('.x > input')[0].value);
    point["y"] = Number(points_elements[i].querySelectorAll('.y > input')[0].value);
    point["heading"] = Number(points_elements[i].querySelectorAll('.heading > input')[0].value)*Math.PI/180;
    point["reverse"] = points_elements[i].querySelectorAll('.reverse > input:checked').value;
    points.push(point);
  }
  return points
}


function draw_path (){
  color = "#ffffff";
  ctx.beginPath();
  ctx.moveTo(0,0);
  for (var i = 0; i < path_points.length; i++){
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc (path_points[i]["x"]*pixel_meters, path_points[i]["y"]*pixel_meters,path_size, 0, 2*Math.PI);
    ctx.fill();
  }
  ctx.closePath();
}

function draw_points () {
  var points = get_points();
  color = "#ffffff";

  for (var i = 0; i < points.length; i++){
    ctx.beginPath();
    ctx.arc (points[i]["x"]*pixel_meters, points[i]["y"]*pixel_meters, point_size, 0, 2*Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.stroke();
  }
}

function init_field() {
  field_canvas = document.getElementById("field");

  ctx = field_canvas.getContext('2d');
  field_img = new Image;
  field_img.onload = function() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    draw_points();
  };
  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
}

function draw_field() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    draw_path();
    draw_points();
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='draw_field()'></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='draw_field()'></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='draw_field()'></td>"+
    "<td class='reverse'><label class='toggle'><input type='checkbox' value='true' checked><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
}

function delete_point (elem) {
  $(elem).parent().parent().remove();
  update_graph();
}

function solve() {
  var points = get_points();
  var params = {}
  params["poly"] = Number(document.getElementById("polynom").value);
  params["pos"] = Number(document.getElementById("position").value);
  params["angle"] = Number(document.getElementById("angle").value);
  params["radius"] = Number(document.getElementById("radius").value);
  params["radius_cont"] = Number(document.getElementById("radius_cont").value);
  params["length"] = Number(document.getElementById("length").value);

  var data = {"params": params, "points":points}
  var data = JSON.stringify(data);
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status){points = JSON.parse(data); alert("solved!"); path_points = points; draw_field();});
}
