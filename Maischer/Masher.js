window.chartColors = {
          red: 'rgb(255, 99, 132)',
          orange: 'rgb(255, 159, 64)',
          yellow: 'rgb(255, 205, 86)',
          green: 'rgb(75, 192, 192)',
          blue: 'rgb(54, 162, 235)',
          purple: 'rgb(153, 102, 255)',
          grey: 'rgb(201, 203, 207)'
        };         
        var ChartConfig = {
                        // The type of chart we want to create
                        type: 'line',

                        // The data for our dataset
                        data: 
                        { 
                          datasets: 
                          [
                            {
                              label: 'Temperature',
                              yAxisID: 'A',
                              backgroundColor: window.chartColors['red'],
                              borderColor: window.chartColors['red'],
                              data: [],
                              fill: false
                            },
                            {
                              label: 'Set Point',
                              yAxisID: 'A',
                              backgroundColor: window.chartColors['orange'],
                              borderColor: window.chartColors['orange'],
                              data: [],
                              fill: false
                            },                            
                            {
                              label: 'Output',
                              yAxisID: 'B',
                              backgroundColor: window.chartColors['green'],
                              borderColor: window.chartColors['green'],
                              data: [],
                              fill: false
                            }                        
                          ] 
                        },

                       // Configuration options go here
                       options: {
                         maintainAspectRatio: false,
                         responsive: true,
                         title: {
                            display: true,
                            text: 'The Masher'
                         },
                         tooltips: {
                            enabled: false,
                            mode: 'index',
                            intersect: false,
                         },    
                         elements: {
                                    point:{
                                        radius: 0
                                    }
                                },                       
                         scales: {
                               xAxes: [{
                                              type: 'time',
                                              time: {
                                                   unit: 'minute',
                                                    displayFormats: {
                                                       minute: 'HH:mm:ss'
                                                   }                                          
                                              },
                                              ticks: {
                                                      autoSkip: true,
                                                      maxTicksLimit: 20
                                                  }                                                 
                                           }],                                
                               yAxes: [
                                        {
                                          id: 'A',
                                          display: true,
                                          position: 'left',
                                            
                                          ticks: {
                                              beginAtZero: true,
                                              suggestedMin: 0,
                                              suggestedMax: 100, 
                                          },                                                                                  
                                          scaleLabel: {
                                             display: true,
                                             labelString: 'Temperature'
                                          }

                                        },       
                                        {
                                        id: 'B',
                                        display: true,
                                        position: 'right',
                                     
                                        ticks: {
                                            beginAtZero: true,
                                            min: 0,
                                            max: 100,
                                        },                                        
                                        scaleLabel: {
                                           display: true,
                                           labelString: 'Output'
                                        }}                                        
                                     ],
                                
                          },
                       }
                   };

        var colorNames = Object.keys(window.chartColors);     
        var openedBrewage = null
        var openedConfiguration = null
        var dontOverwriteTempSp = false
        function CreateJsonCommand(command){
          var obj = new Object();
          obj.Command = command;
          return obj
        }

        function GetBrewages(){
          var handleGetBrewagesAnswer = function (jsonobj) {
            var selectList = document.getElementById("BrewageList");
             //Create and append the options
             for (var i = 0; i < jsonobj.Brewages.length; i++) {
                 var option = document.createElement("option");
                 option.setAttribute("value", jsonobj.Brewages[i]);
                 option.text = jsonobj.Brewages[i];
                 selectList.appendChild(option);
             }
             document.getElementById("pbOpenBrewage").disabled = false;
          }

          cmd = CreateJsonCommand("GetBrewages")
          WebSocketClient(cmd,handleGetBrewagesAnswer)
        }

        function OpenBrewage(){
          var handleOpenBrewageAnswer = function (jsonobj) {

            console.log(jsonobj); 
            openedBrewage = jsonobj;
            openedConfiguration = jsonobj.Configuration
            ReloadConfiguration();

            document.getElementById("BrewageList").disabled = true;
            document.getElementById("pbOpenBrewage").disabled = true;
            document.getElementById("pbShowConfiguration").disabled = false;
            document.getElementById("pbStartPID").disabled = false;
            document.getElementById("selectBrewagePopup").style.display = "none";

            document.getElementById("headerText").innerHTML = document.getElementById("BrewageList").value;


          }
          var selectList = document.getElementById("BrewageList");
          var selectedDatabase = selectList.options[selectList.selectedIndex].text;

          cmd = CreateJsonCommand("OpenBrewage")
          cmd.Brewage = selectedDatabase
          WebSocketClient(cmd,handleOpenBrewageAnswer)
        }

        var intervalID = null
        function StartGetMeasurements(cb){
          if (cb.checked){
             intervalID = setInterval(GetMeasurement, 1000);
          }else{
            clearInterval(intervalID)
          }
        }

        function GetMeasurement(){
          var handleGetMeasurementAnswer = function (jsonobj) {
            document.getElementById("TemperatureSP").innerHTML = jsonobj.TemperatureSetPoint + ' °C'
            window.gauge.value = jsonobj.TemperatureProcessValue;
            window.gauge.update();
            ChartConfig.data.datasets[0].data.push({
                        x: new Date(Date.now()),
                        y: jsonobj.TemperatureProcessValue })

            ChartConfig.data.datasets[1].data.push({
                        x: new Date(Date.now()),
                        y: jsonobj.TemperatureSetPoint })

            ChartConfig.data.datasets[2].data.push({
                                              x: new Date(Date.now()),
                                              y: jsonobj.OutputPV })
            window.myLine.update();
          }

          cmd = CreateJsonCommand("GetMeasurement")
          WebSocketClient(cmd,handleGetMeasurementAnswer)
        }

        function SetTemperature(){
          var setPoint = document.getElementById("TemperatureSP").value;          

          var handleSetTemperatureAnswer = function (jsonobj) {
            document.getElementById("TemperatureSP").value = jsonobj.SetPoint
          }

          cmd = CreateJsonCommand("SetTemperature")
          cmd.SetPoint = setPoint
          WebSocketClient(cmd,handleSetTemperatureAnswer)
        }

        function SetMotorAngle(){
          var motorAngle = document.getElementById("MotorAngleSP").value;          

          var handleSetMotorAngleAnswer = function (jsonobj) {
            GetMotorAngle()
          }

          cmd = CreateJsonCommand("SetMotorAngle")
          cmd.Angle = motorAngle
          WebSocketClient(cmd,handleSetMotorAngleAnswer)
        }

        function GetMotorAngle(){
          var handleGetMotorAngleAnswer = function (jsonobj) {
            document.getElementById("MotorAnglePV").value = jsonobj.Angle
            if(document.getElementById("MotorAnglePV").value != document.getElementById("MotorAngleSP").value){
              setTimeout(GetMotorAngle, 1000); //Clear the flag after 4 seconds
            }
          }

          cmd = CreateJsonCommand("GetMotorAngle")
          WebSocketClient(cmd,handleGetMotorAngleAnswer)
        }

        function ZeroMotorAngle(){
          var handleZeroMotorAngleAnswer = function (jsonobj) {
          }

          cmd = CreateJsonCommand("ZeroMotorAngle")
          WebSocketClient(cmd,handleZeroMotorAngleAnswer)
        }

        /*
        function SetOutput(){
          var setPoint = document.getElementById("OutputSP").value;          
          var handleSetOutputAnswer = function (jsonobj) {
            document.getElementById("OutputSP").value = jsonobj.Output;
          }
          WebSocketClient("SetOutput " + setPoint,handleSetOutputAnswer)
        }*/


        function StartRegelaar(){
          var handleStartRegelaarAnswer = function (jsonobj) {
            document.getElementById("pbStopPID").disabled = false;
            document.getElementById("pbStartPID").disabled = true;
            if(intervalID == null){
              GetMeasurement();
              intervalID = setInterval(GetMeasurement, 1000);
            }
          }
          cmd = CreateJsonCommand("StartStop")
          cmd.Start = true
          WebSocketClient(cmd,handleStartRegelaarAnswer)
        }

        function StopRegelaar(){
          var handleStopRegelaarAnswer = function (jsonobj) {
            document.getElementById("pbStopPID").disabled = true;
            document.getElementById("pbStartPID").disabled = false;

            if(intervalID != null){
              clearInterval(intervalID)
            }
          }
          cmd = CreateJsonCommand("StartStop")
          cmd.Start = false
          WebSocketClient(cmd,handleStopRegelaarAnswer)
        }

        function WebSocketClient(jsonCommandToSend,messageHandler) {
          if ("WebSocket" in window) {
            // Let us open a web socket
            commandToSend = JSON.stringify(jsonCommandToSend);          
            var ws = new WebSocket("ws://localhost:7654"); //192.168.178.21
            ws.onopen = function() {
              ws.send(commandToSend);
            };                   // Web Socket is connected, send data using send()
            ws.onmessage = function(evt) {
                var received_msg = evt.data;
                //alert(received_msg)
                var jsonobj = JSON.parse(received_msg)                  
                messageHandler(jsonobj)
            };

            ws.onclose = function() { 
            };

            ws.onerror = function(evt) {
              alert('ws normal error: ' + evt.type);
            };  
          } else {
              // The browser doesn't support WebSocket
              alert("WebSocket NOT supported by your Browser!");
          }                       
        }

/**************************************************************************************/
/*      Configuration       */

        function SetConfiguration(){
          var handleSetOutputAnswer = function (jsonobj) {
            openedConfiguration = jsonobj
            ReloadConfiguration()
          }
          console.log("SetConfiguration")
          cmd = CreateJsonCommand("SetConfiguration")
          cmd.Configuration = new Object();
          cmd.Configuration.ConfigurationId   = document.getElementById("Configuration_Id").value;
          cmd.Configuration.ConfigurationName = document.getElementById("Configuration_Name").value;
          cmd.Configuration.P = document.getElementById("Configuration_P").value;
          cmd.Configuration.I = document.getElementById("Configuration_I").value;
          cmd.Configuration.D = document.getElementById("Configuration_D").value;
          cmd.Configuration.StepsPerRevolution = document.getElementById("Configuration_StepsPerRevolution").value;

          WebSocketClient(cmd, handleSetOutputAnswer)
        }

        function SaveConfiguration(){
          SetConfiguration();
          CloseConfiguration();
        }

        function CloseConfiguration(){
          document.getElementById("configurationPopup").style.display = "none";
        }

        function ReloadConfiguration(){
          if ( openedConfiguration != null)
          {
            document.getElementById("Configuration_Id").value   = openedConfiguration.ConfigurationId;
            document.getElementById("Configuration_Name").value = openedConfiguration.ConfigurationName;
            document.getElementById("Configuration_P").value    = openedConfiguration.P;
            document.getElementById("Configuration_I").value    = openedConfiguration.I;
            document.getElementById("Configuration_D").value    = openedConfiguration.D;
            document.getElementById("Configuration_StepsPerRevolution").value = openedConfiguration.StepsPerRevolution;
          }
        }

        window.onload = function() {
            //alert("Reload")

            var ctx = document.getElementById("myChart").getContext('2d');
            // ctx.height = 500;
            window.myLine = new Chart(ctx, ChartConfig);   

            // Show the share pop up window when the share icon is clicked
            document.getElementById("pbShowConfiguration").addEventListener("click", function(){
              document.getElementById("configurationPopup").style.display = "inline";
            });

            window.gauge = new RadialGauge({
                renderTo: 'tempGauge',
                width: 300,
                height: 300,
                units: "°C",
                minValue: 0,
                startAngle: 50,
                ticksAngle: 260,
                valueBox: true,
                maxValue: 120,
                majorTicks: [
                    "0",
                    "20",
                    "40",
                    "60",
                    "80",
                    "100",
                    "120"
                ],
                minorTicks: 2,
                strokeTicks: true,
                highlights: [
                    {
                        "from": 95,
                        "to": 120,
                        "color": "rgba(200, 50, 50, .75)"
                    }
                ],
                colorPlate: "#fff",
                borderShadowWidth: 0,
                borders: false,
                needleType: "arrow",
                needleWidth: 2,
                needleCircleSize: 7,
                needleCircleOuter: true,
                needleCircleInner: false,
                animationDuration: 500,
                animationRule: "linear"
            }).draw();
            GetBrewages()

            // var intervalID = setInterval(GetTemperature, 1000);
            // var intervalID = setInterval(GetServoAngle, 1000);
            // var intervalID = setInterval(GetOutput, 1000);
        };