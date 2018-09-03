var data = ""
var ctx;
var field_img;
var field_canvas;
var pixel_meters;

var path_points = [];
var costs = [];

const point_size = 5;
const path_size = 1;
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
    point["reverse"] = String(points_elements[i].querySelectorAll('.reverse > label > input')[0].checked);
    points.push(point);
  }
  return points
}


function draw_path (){
  ctx.beginPath();
  ctx.moveTo(0,0);
  for (var i = 0; i < path_points.length; i++){
    var val = parseInt(i*100/path_points.length);
    color = "hsl("+val+",100%,60%)";
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
  //  ctx.stroke();
  }
}

function init_field() {
  field_canvas = document.getElementById("field");

  ctx = field_canvas.getContext('2d');
  field_img = new Image;
  field_img.onload = function() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowColor = '#101010';
    ctx.shadowBlur = 10;
    draw_points();
  };
  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
  
}

function draw_field() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowBlur = 0;
    ctx.imageSmoothingEnabled = false;
    draw_path();
    ctx.imageSmoothingEnabled = false;
    ctx.shadowBlur = 10;
    draw_points();
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='draw_field()' value=1></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='draw_field()' value=1></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='draw_field()' value=0></td>"+
    "<td class='reverse'><label class='toggle'><input type='checkbox' value='true'><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
}

function update_costs () {
  document.getElementById("pos_cost_val").innerHTML = costs["pos_cost"].toPrecision(3);
  document.getElementById("angle_cost_val").innerHTML = costs["angle_cost"].toPrecision(3);
  document.getElementById("radius_cost_val").innerHTML = costs["radius_cost"].toPrecision(3);
  document.getElementById("radius_cont_cost_val").innerHTML = costs["radius_cont_cost"].toPrecision(3);
  document.getElementById("length_cost_val").innerHTML = costs["length_cost"].toPrecision(3);
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
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status){
    var parsed_data = JSON.parse(data);
    path_points = []
    for (var i = 0; i < parsed_data.length; i++) {
      path_points = path_points.concat(parsed_data[i]["path_points"]);
    }
    console.log("total:");
    console.log(path_points);
    //costs = parsed_data["costs"];
    draw_field();
    //update_costs();
  });
}
