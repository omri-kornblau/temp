var ctx;
var field_img;
var field_canvas;
var points = [];
var point_size = 20;
/*function save_data() {
  data = "";
  points = [];
  $('tbody').children('tr').each(function() {
    let xp = parseFloat($($($(this).children()).children()[0]).val());
    let yp = parseFloat($($($(this).children()).children()[1]).val());
    let heading = parseFloat($($($(this).children()).children()[2]).val());
    if (isNaN(heading)) {
      heading = 0;
    }
    if (isNaN(xp)) {
      xp = 0;
    }
    if (isNaN(yp)) {
      yp = 0;
    }
    let reverse = ($($($(this).children()).children()[5]).prop('checked'));
    data += xp + "," + yp + "," + heading + ";";
    points.push({x: xp, y: yp});
    //$('#points').append("<tr class='point move-cursor'><td>"+xp+","+yp+"</td></tr>");
    });

}*/

function load_data(){

}

function update_graph() {

}

function init_field() {
  var field_canvas = document.getElementById("field");

  ctx = field_canvas.getContext('2d');
  field_img = new Image;
  field_img.onload = function() {
    ctx.drawImage(field_img, 0, 0, field_img.width, field_img.height, 0, 0, field_canvas.width, field_canvas.height);
  };
  field_img.src = 'static/img/field_background.png';
}

function draw_points (){
  points = [{x: 20, y:20},{x: 20, y:20},{x: 2, y:4}]; 
  color = "#2CFF2C";
  ctx.fillstyle = color;
  //for (var i = 0; i < points.length; i++){
    alert(points[1]["x"]);
    ctx.beginPath();
    //ctx.moveTo(0, 0);
    ctx.arc (20,points[0]["Y"],point_size,0,2*Math.PI);
    //ctx.arc (points[1]["x"], points[1]["Y"], point_size, 0, Math.PI * 2, true);
    ctx.stroke();
    ctx.fill();
    ctx.closePath();

  //}
}

function add_point () {
  $('#points').append("<tr class='point move-cursor' class='point'>"+
    "<td class='x'><input class='form-control form-control-small' type='number' placeholder='X' oninput='update_graph()'></td>"+
    "<td class='y'><input class='form-control form-control-small' type='number' placeholder='Y' oninput='update_graph()'></td>"+
    "<td class='heading'><input class='form-control form-control-small' type='number' placeholder='α' oninput='update_graph()'></td>"+
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
  var points_elements = document.getElementsByClassName("point");
  var points = [];
  for (var i = 0; i < points_elements.length; i++) {
    var point = {};
    point["x"] = points_elements[i].querySelectorAll('.x > input')[0].value;
    point["y"] = points_elements[i].querySelectorAll('.y > input')[0].value;
    point["heading"] = points_elements[i].querySelectorAll('.heading > input')[0].value;
    point["reverse"] = points_elements[i].querySelectorAll('.reverse > input:checked').value;
    points.push(point);
  }
  var data = JSON.stringify(points);
  $.post("SOLVE", {params: data}, function(){});
}