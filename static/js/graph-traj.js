var resetVelFnc;
var resetAccFnc;

function show_graph () {
  clicked_graph = !clicked_graph
  if (clicked_graph) {
    $(".traj-area").hide(200)
  }
  else {
    $(".traj-area").show(200) 
    
    setTimeout(function() {
      draw_traj();        
    }, 200);
  }
}

function draw_traj () {
  new Chartist.Line('#vel-chart', {
    labels: [get_traj_data()["time"]],
    series: [
      setToGraph(get_traj_data()["time"], get_traj_data()["right_vel"]),
      setToGraph(get_traj_data()["time"], get_traj_data()["left_vel"])
    ],}, {
    axisX: {
      type: Chartist.AutoScaleAxis,
      showGrid: false,
      showLabel: false,
    },
    plugins: [
      Chartist.plugins.zoom({onZoom : onZoomVel})//{ onZoom: onZoom })
    ],
    chartPadding: {
      right: 40
    }
    });

    new Chartist.Line('#acc-chart', {
    labels: [get_traj_data()["time"]],
    series: [
      setToGraph(get_traj_data()["time"], get_traj_data()["right_acc"]),
      setToGraph(get_traj_data()["time"], get_traj_data()["left_acc"])
    ],}, {
    axisX: {
      type: Chartist.AutoScaleAxis,
      showGrid: false,
      showLabel: true,
    },
      labels: [get_traj_data()["time"],get_traj_data()["time"]],
    plugins: [
      Chartist.plugins.zoom({onZoom : onZoomAcc})//{ onZoom: onZoom })
    ],
    chartPadding: {
      right: 40
    }
    });
}

function onZoomVel(chart, reset) {
  resetVelFnc = reset;
  $('#vel-zoom-icon').show(200);
}

function onZoomAcc(chart, reset) {
  resetAccFnc = reset;
  $('#acc-zoom-icon').show(200);
}

function resetVelGraph () {
  resetVelFnc && resetVelFnc();
  resetVelFnc = null;
  $('#vel-zoom-icon').hide(200);
}

function resetAccGraph () {
  resetAccFnc && resetAccFnc();
  resetAccFnc = null;
  $('#acc-zoom-icon').hide(200);
}