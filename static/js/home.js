//var data = "";
var ctx;
var field_img;
var field_canvas;
var pixel_meters;

const default_data = [{"path_points":[],"scalars_x":[null], "scalars_y":[null]}]

var parsed_data = [default_data]; //stores all the data got from python 
var data_version = 0; //stores current data version
var new_solve = true;

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
    point["switch"] = String(points_elements[i].querySelectorAll('.switch > label > input')[0].checked);
    points.push(point);
  }
  return points
}

function draw_path (points){
  ctx.beginPath();
  ctx.moveTo(0,0);
  for (var i = 0; i < points.length; i++){
    var val = parseInt(i*100/points.length);
    color = "hsl("+val+",100%,60%)";
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc (points[i]["x"]*pixel_meters, points[i]["y"]*pixel_meters,path_size, 0, 2*Math.PI);
    ctx.fill();
  }
  ctx.closePath();
}

function draw_points (points) {
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
  $("#loader").hide();

  field_canvas = document.getElementById("field");

  ctx = field_canvas.getContext('2d');
  field_img = new Image;
  field_img.onload = function() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowColor = '#101010';
    ctx.shadowBlur = 10;
    draw_points(get_points());
  };
  field_img.src = 'static/img/field_background.png';
  pixel_meters = field_canvas.width/real_field_width;
}

function get_data () {
  return(parsed_data[data_version]);
}

function draw_field() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
    ctx.shadowBlur = 0;

    for (var i = 0; i < get_data().length; i++) {
      draw_path(get_data()[i]["path_points"]);
    }
    
    ctx.shadowBlur = 10;
    draw_points(get_points());
}

function update_costs () {
  /* Missing here: 'for' loop to handle multiple paths costs*/
  document.getElementById("pos_cost_val").innerHTML = get_data()[0]["costs"]["pos_cost"].toPrecision(3);
  document.getElementById("angle_cost_val").innerHTML = get_data()[0]["costs"]["angle_cost"].toPrecision(3);
  document.getElementById("radius_cost_val").innerHTML = get_data()[0]["costs"]["radius_cost"].toPrecision(3);
  document.getElementById("radius_cont_cost_val").innerHTML = get_data()[0]["costs"]["radius_cont_cost"].toPrecision(3);
  document.getElementById("length_cost_val").innerHTML = get_data()[0]["costs"]["length_cost"].toPrecision(3);
}

//delete future changes and push new version of paths
function new_version (push_item) {
  if (data_version < parsed_data.length) {
      parsed_data.splice(data_version+1, parsed_data.length);
    }
  parsed_data.push(push_item);
  data_version++;
  draw_field();
}

function reset_version() {
  data_version = 0;
  draw_field();
}

function redo_change () {
  if (data_version < parsed_data.length-1) {
    data_version ++;
    draw_field();
    update_costs();
  }
}

function undo_change () {
  if (data_version > 0) {
    data_version --;
    draw_field();
    update_costs();
  }
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='draw_field()' value=1></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='draw_field()' value=1></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='draw_field()' value=0></td>"+
    "<td class='switch'><label class='toggle'><input type='checkbox' value='true'><span class='handle'></span></label></td>"+
    "<td class='delete'><a class='btn btn-danger btn-small' onclick='delete_point(this)'>"+
    "<i class='glyphicon glyphicon-trash glyphicon-small'></i>"+
    "</a></td>"+
    "</tr>");
  new_version(default_data);
  new_solve = true;

  //----------temporary!!!---------------
  data_version = 0;
  parsed_data = [default_data];
}

function delete_point (elem) {
  $(elem).parent().parent().remove();
  new_version(default_data);
  new_solve = true;

  //----------temporary!!!---------------
  data_version = 0;
  parsed_data = [default_data];
}


function solve() {
  var points = get_points();
  var params = {};
  
  params["poly"] = Number(document.getElementById("polynom").value);
  params["pos"] = Number(document.getElementById("position").value);
  params["angle"] = Number(document.getElementById("angle").value);
  params["radius"] = Number(document.getElementById("radius").value);
  params["radius_cont"] = Number(document.getElementById("radius_cont").value);
  params["length"] = Number(document.getElementById("length").value);

  var data=[];
  var start = 0;
  var path_num = 0;

  for(var i = 0; i < points.length; i++)  {
    if (i == points.length - 1) {

      data.push({
        "params": params, 
        "points":points.slice(start),
        "scalars_x":get_data()[path_num]["scalars_x"], 
        "scalars_y":get_data()[path_num]["scalars_y"],});
      }

    if (points[i]["switch"]  == "true") {   
      data.push({
        "params": params, 
        "points":points.slice(start, i + 1),
        "scalars_x":get_data()[path_num]["scalars_x"], 
        "scalars_y":get_data()[path_num]["scalars_y"],});
      start = i;
    
      if (!new_solve) {
        path_num++;
      }  
    }
  }

  $("#loader").show(700);
  
  var data = JSON.stringify(data);
  $.post("http://127.0.0.1:3000/", {"data": data}, function(data, status) {
    $("#loader").hide(1000);

    new_solve = false;
    new_version(JSON.parse(data));
    update_costs();
  });
}
