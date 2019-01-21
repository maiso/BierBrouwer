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
                              label: 'Temperatuur',
                              yAxisID: 'A',
                              backgroundColor: window.chartColors['red'],
                              borderColor: window.chartColors['red'],
                              data: [],
                              fill: false
                            },
                            {
                              label: 'Output',
                              yAxisID: 'B',
                              backgroundColor: window.chartColors['purple'],
                              borderColor: window.chartColors['purple'],
                              data: [],
                              fill: false
                            },
                            {
                              label: 'Servo Output',
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
                            text: 'De Maischter'
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
                                          scaleLabel: {
                                             display: true,
                                             labelString: 'Temperatuur'
                                          }
                                        },       
                                        {
                                        id: 'B',
                                        display: true,
                                        position: 'right',
                                        scaleLabel: {
                                           display: true,
                                           labelString: 'Servo & Output'
                                        }}                                        
                                     ],
                                
                          },
                       }
                   };
        var colorNames = Object.keys(window.chartColors);     
        var openedBrewage = null
        var openedConfiguration = null

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
          }
          var selectList = document.getElementById("BrewageList");
          var selectedDatabase = selectList.options[selectList.selectedIndex].text;

          cmd = CreateJsonCommand("OpenBrewage")
          cmd.Brewage = selectedDatabase
          WebSocketClient(cmd,handleOpenBrewageAnswer)
        }

        function GetSetPoint(){
          var handleGetSetPointAnswer = function (jsonobj) {
            document.getElementById("TemperatuurPV").value = jsonobj.SetPoint
          }
          WebSocketClient("GetSetPoint",handleGetSetPointAnswer)
        }

        function SetTemperatuur(){
          var setPoint = document.getElementById("TemperatuurSP").value;          
          //alert("SetTemperatuur " + setPoint)

          var handleSetTemperatuurAnswer = function (jsonobj) {
            document.getElementById("TemperatuurSP").value = jsonobj.SetPoint
          }
          WebSocketClient("SetTemperatuur " + setPoint,handleSetTemperatuurAnswer)
        }

        function GetTemperatuur(){
          var handleGetTemperatuurAnswer = function (jsonobj) {
            document.getElementById("TemperatuurPV").value = jsonobj.Temperatuur

            ChartConfig.data.datasets[0].data.push({
                                              x: new Date(Date.now()),
                                              y: jsonobj.Temperatuur })
            window.myLine.update();
          }
          WebSocketClient("GetTemperatuur",handleGetTemperatuurAnswer)
        }

        function GetServoAngle(){
          var handleGetServoAngleAnswer = function (jsonobj) {
            document.getElementById("ServoAnglePV").value = jsonobj.ServoAngle
            ChartConfig.data.datasets[2].data.push({
                                              x: new Date(Date.now()),
                                              y: jsonobj.ServoAngle })
            window.myLine.update();            
          }
          WebSocketClient("GetServoAngle",handleGetServoAngleAnswer)
        }

        function SetOutput(){
          var setPoint = document.getElementById("OutputSP").value;          
          var handleSetOutputAnswer = function (jsonobj) {
            document.getElementById("OutputSP").value = jsonobj.Output;
          }
          WebSocketClient("SetOutput " + setPoint,handleSetOutputAnswer)
        }

        function GetOutput(){
          var handleGetOutputAnswer = function (jsonobj) {
            document.getElementById("OutputPV").value = jsonobj.OutputPV;
            ChartConfig.data.datasets[1].data.push({
                                              x: new Date(Date.now()),
                                              y: jsonobj.OutputPV })
            window.myLine.update();
          }
          WebSocketClient("GetOutput",handleGetOutputAnswer)
        }

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
          cmd.Configuration.NrOfSteps = document.getElementById("Configuration_NrOfSteps").value;

          WebSocketClient(cmd, handleSetOutputAnswer)
        }

        function StartRegelaar(){
          var handleStartRegelaarAnswer = function (jsonobj) {
          }
          WebSocketClient("Regelaar Start",handleStartRegelaarAnswer)
        }

        function StopRegelaar(){
          var handleStopRegelaarAnswer = function (jsonobj) {
          }
          WebSocketClient("Regelaar Stop",handleStopRegelaarAnswer)
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

        function SaveConfiguration(){
          SetConfiguration();
          CloseConfiguration();
        }

        function CloseConfiguration(){
          document.getElementById("configurationPopup").style.display = "none";
        }
        /**************************************************************

        */


        function ReloadConfiguration(){
          if ( openedConfiguration != null)
          {
            document.getElementById("Configuration_Id").value   = openedConfiguration.ConfigurationId;
            document.getElementById("Configuration_Name").value = openedConfiguration.ConfigurationName;
            document.getElementById("Configuration_P").value    = openedConfiguration.P;
            document.getElementById("Configuration_I").value    = openedConfiguration.I;
            document.getElementById("Configuration_D").value    = openedConfiguration.D;
            document.getElementById("Configuration_NrOfSteps").value = openedConfiguration.NrOfSteps;
          }
        }

        window.onload = function() {
            //alert("Reload")

            var ctx = document.getElementById("myChart").getContext('2d');
            ctx.height = 500;
            window.myLine = new Chart(ctx, ChartConfig);   

            // Show the share pop up window when the share icon is clicked
            document.getElementById("pbShowConfiguration").addEventListener("click", function(){
              document.getElementById("configurationPopup").style.display = "inline";
            });

            GetBrewages()

            // GetSetPoint()
            // GetTemperatuur()
            // GetServoAngle()
            // GetOutput()

            // var intervalID = setInterval(GetTemperatuur, 1000);
            // var intervalID = setInterval(GetServoAngle, 1000);
            // var intervalID = setInterval(GetOutput, 1000);
        };