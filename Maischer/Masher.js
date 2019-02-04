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

        function addItemToSelectList(selectList, text){
          var option = document.createElement("option");
          option.setAttribute("value", text);
          option.text = text;
          selectList.appendChild(option);
        }

        function emptySelectListOptions(selectList)
        {
            var i;
            for(i = selectList.options.length - 1 ; i >= 0 ; i--)
            {
                selectList.remove(i);
            }
        }

        function insertAllMeasurements(jsonobj){
            for (var i = 0; i < jsonobj.Measurments.length; i++) {
              var measurment = jsonobj.Measurments[i]
              insertDataInChart(measurment.MeasurementTime,measurment.Temperature,measurment.SetPoint,measurment.PIDOutput)
            }
            window.myLine.update();
        }
/**************************************************************************************/
/*      Brewage Selection      */

        function GetActiveBrew(){
            var handleGetActiveBrewAnswer = function (jsonobj) {
              if(jsonobj['Brewage'] == null){
                  //No active brewage found, show select popup
                  GetAvailableSettings();
                  document.getElementById("selectBrewagePopup").style.display = "inline";
                  userControl(jsonobj.ControllerMode)
              } 
              else {
                //Found an active brewage, insert the measurments into the graph
                insertAllMeasurements(jsonobj)

                addItemToSelectList(document.getElementById("BrewageList"),jsonobj.Brewage);

                OpenBrewage()
                userControl(jsonobj.ControllerMode)
              }
              document.getElementById("pbOpenBrewage").disabled = false;
              document.getElementById("loadingActiveBrewPopup").style.display = "none";
          }

          cmd = CreateJsonCommand("GetActiveBrew")
          WebSocketClient(cmd,handleGetActiveBrewAnswer)

        }

        function GetAvailableSettings(){
          var handleGetAvailableSettingsAnswer = function (jsonobj) {
            console.log(jsonobj);
            var selectList = document.getElementById("BrewageList");
             //Create and append the options
             emptySelectListOptions(selectList)
             for (var i = 0; i < jsonobj.Brewages.length; i++) {
                addItemToSelectList(document.getElementById("BrewageList"),jsonobj.Brewages[i]);
             }

             var selectList = document.getElementById("newBrew_ConfigSelect");
             //Create and append the options
             emptySelectListOptions(selectList)
             for (var i = 0; i < jsonobj.Configurations.length; i++) {
                addItemToSelectList(document.getElementById("newBrew_ConfigSelect"),jsonobj.Configurations[i]);
             }

              // TODO add mashing schemas
             document.getElementById("pbOpenBrewage").disabled = false;
          }

          cmd = CreateJsonCommand("GetAvailableSettings")
          WebSocketClient(cmd,handleGetAvailableSettingsAnswer)
        }

        function OpenBrewage(){
          var handleOpenBrewageAnswer = function (jsonobj) {

            console.log(jsonobj); 
            openedBrewage = jsonobj;
            openedConfiguration = jsonobj.Configuration
            ReloadConfiguration();

            userControl(jsonobj.ControllerMode);

            document.getElementById("BrewageList").disabled = true;
            document.getElementById("pbOpenBrewage").disabled = true;
            document.getElementById("pbShowConfiguration").disabled = false;
            document.getElementById("selectBrewagePopup").style.display = "none";

            document.getElementById("headerText").innerHTML = document.getElementById("BrewageList").value;

            if (jsonobj.ControllerMode != "Stopped"){
              StartGetMeasurements();
            }
            else{
              GetAllMeasurements();
            }
          }
          var selectList = document.getElementById("BrewageList");
          var selectedDatabase = selectList.options[selectList.selectedIndex].text;

          cmd = CreateJsonCommand("OpenBrewage")
          cmd.Brewage = selectedDatabase
          WebSocketClient(cmd,handleOpenBrewageAnswer)
        }

        function NewBrewage(){
          var handleNewBrewageAnswer = function (jsonobj) {
            addItemToSelectList(document.getElementById("BrewageList"),jsonobj['BrewName'])
              var sel = document.getElementById('BrewageList');
              var val = jsonobj['BrewName'];
              for(var i = 0, j = sel.options.length; i < j; ++i) {
                  if(sel.options[i].value === val) {
                     sel.selectedIndex = i;
                     break;
                  }
              }
          

            OpenBrewage()
          }
          cmd = CreateJsonCommand("NewBrewage")
          cmd.Brewage = new Object();
          cmd.Brewage.BrewName          = document.getElementById("newBrew_Name").value;
          cmd.Brewage.ConfigurationName = document.getElementById("newBrew_ConfigSelect").value;
          WebSocketClient(cmd, handleNewBrewageAnswer)          
        }

/**************************************************************************************/
/*      Other stuff       */

        var intervalID = null
        function StartGetMeasurements(){
          if (intervalID == null){
            GetMeasurement();
            intervalID = setInterval(GetMeasurement, 1000);
          }
          // else{
          //   clearInterval(intervalID)
          // }
        }

        function insertDataInChart(date,tempPv,tempSp,Output) {
              ChartConfig.data.datasets[0].data.push({ x: date, y: tempPv });
              ChartConfig.data.datasets[1].data.push({ x: date, y: tempSp});
              ChartConfig.data.datasets[2].data.push({ x: date, y: Output });
        }

        function GetMeasurement(){
          var handleGetMeasurementAnswer = function (jsonobj) {
            document.getElementById("TemperatureSP").innerHTML = jsonobj.TemperatureSetPoint + ' °C'
            window.gauge.value = jsonobj.TemperatureProcessValue;
            window.gauge.update();

            userControl(jsonobj.ControllerMode)
            console.log(jsonobj); 
            if (jsonobj.ControllerMode == "Started"){
                insertDataInChart(new Date(Date.now()), jsonobj.TemperatureProcessValue,jsonobj.TemperatureSetPoint,jsonobj.OutputPV);
                window.myLine.update();
              }
          }

          cmd = CreateJsonCommand("GetMeasurement")
          WebSocketClient(cmd,handleGetMeasurementAnswer)
        }

        function GetAllMeasurements(){
          var handleGetAllMeasurementsAnswer = function (jsonobj) {
            insertAllMeasurements(jsonobj);
          }
          cmd = CreateJsonCommand("GetAllMeasurements")
          WebSocketClient(cmd,handleGetAllMeasurementsAnswer)
        }



        function SetpointInc(){
          console.log("SetpointInc"); 

          var setPoint = document.getElementById("TemperatureSP").innerHTML;
          setPoint = setPoint.substring(0, setPoint.length - 3); 
          setPointFloat = parseFloat(setPoint) + 1
          if(!isNaN(setPointFloat))
            SetTemperature(setPointFloat);
        }
        function SetpointDec(){
          console.log("SetpointDecc"); 

          var setPoint = document.getElementById("TemperatureSP").innerHTML;
          setPoint = setPoint.substring(0, setPoint.length - 3); 
          setPointFloat = parseFloat(setPoint) - 1
          if(!isNaN(setPointFloat))
            SetTemperature(setPointFloat);        
        }

        function SetTemperature(setPoint){
          var handleSetTemperatureAnswer = function (jsonobj) {
            document.getElementById("TemperatureSP").innerHTML = jsonobj.SetPoint + ' °C'
          }

          cmd = CreateJsonCommand("SetTemperature")
          cmd.SetPoint = setPoint
          console.log("SetTemperature"); 

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
            document.getElementById("MotorAnglePV").value = jsonobj.Angle;
            if(document.getElementById("MotorAnglePV").value != document.getElementById("MotorAngleSP").value){
              setTimeout(GetMotorAngle, 1000);
            }
          }

          cmd = CreateJsonCommand("GetMotorAngle");
          WebSocketClient(cmd,handleGetMotorAngleAnswer);
        }

        function ZeroMotorAngle(){
          var handleZeroMotorAngleAnswer = function (jsonobj) {
            document.getElementById("MotorAngleSP").value = 0;
            document.getElementById("pbMotorMax").disabled = false;
            
            GetMotorAngle();
          }

          cmd = CreateJsonCommand("ZeroMotorAngle");
          WebSocketClient(cmd,handleZeroMotorAngleAnswer);
        }

        function MaxMotorAngle(){
          var handleMaxMotorAngleAnswer = function (jsonobj) {
            GetMotorAngle();
          }

          cmd = CreateJsonCommand("MaxMotorAngle");
          WebSocketClient(cmd,handleMaxMotorAngleAnswer);
        }

        function userControl(activeMeasurment){
          if (activeMeasurment == "NotStarted"){
            document.getElementById("pbStartPID").disabled = false;
            document.getElementById("pbPauzePID").disabled = true;
            document.getElementById("pbStopPID").disabled  = true;
            document.getElementById("tempUp").disabled     = false;
            document.getElementById("tempDown").disabled   = false;
          }else if (activeMeasurment == "Started"){
            document.getElementById("pbStartPID").disabled = true;
            document.getElementById("pbPauzePID").disabled = false;
            document.getElementById("pbStopPID").disabled  = false;
            document.getElementById("tempUp").disabled     = false;
            document.getElementById("tempDown").disabled   = false;
          }else if (activeMeasurment == "Pauzed"){
            document.getElementById("pbStartPID").disabled = false;
            document.getElementById("pbPauzePID").disabled = true;
            document.getElementById("pbStopPID").disabled  = false;
            document.getElementById("tempUp").disabled     = false;
            document.getElementById("tempDown").disabled   = false;
          }else if (activeMeasurment == "Stopped"){
            document.getElementById("pbStartPID").disabled = true;
            document.getElementById("pbPauzePID").disabled = true;
            document.getElementById("pbStopPID").disabled  = true;          
            document.getElementById("tempUp").disabled     = true;
            document.getElementById("tempDown").disabled   = true;
          }
        }
        function ControllerStart(){
          var handleControllerStartAnswer = function (jsonobj) {
            if ( jsonobj.Result == 'Ok') {
              userControl(jsonobj.ControllerMode);
              StartGetMeasurements();
            }else{
              alert("Error:" + jsonobj.Message);
            }
            
          }
          cmd = CreateJsonCommand("ControllerMode")
          cmd.Mode = "Start"
          WebSocketClient(cmd,handleControllerStartAnswer)
        }

        function ControllerPauze(){
          var handleControllerPauzeAnswer = function (jsonobj) {
              userControl(jsonobj.ControllerMode)
          }
          cmd = CreateJsonCommand("ControllerMode")
          cmd.Mode = "Pauze"
          WebSocketClient(cmd,handleControllerPauzeAnswer)
        }

        function ControllerStop(){
          var handleControllerStopAnswer = function (jsonobj) {
              userControl(jsonobj.ControllerMode)
          }
          cmd = CreateJsonCommand("ControllerMode")
          cmd.Mode = "Stop"
          WebSocketClient(cmd,handleControllerStopAnswer)
        }

        function WebSocketClient(jsonCommandToSend,messageHandler) {
          if ("WebSocket" in window) {
            // Let us open a web socket
            commandToSend = JSON.stringify(jsonCommandToSend);          
            var ws = new WebSocket("ws://"+window.location.hostname+":7654"); //192.168.178.21
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

        function GetConfiguration(){
          var handleGetConfigurationAnswer = function (jsonobj) {
            openedConfiguration = jsonobj
            ReloadConfiguration()
          }

          cmd = CreateJsonCommand("GetConfiguration")
          cmd.ConfigurationName = document.getElementById("newBrew_ConfigSelect").value;
          WebSocketClient(cmd,handleGetConfigurationAnswer)
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
          cmd.Configuration.StepsPerRevolution = document.getElementById("Configuration_StepsPerRevolution").value;

          WebSocketClient(cmd, handleSetOutputAnswer)
        }

        function OpenExistingConfiguration(){
          GetConfiguration()
          ShowConfigurationPopup();
        }

        function NewConfiguration(){
          openedConfiguration = null
          ShowConfigurationPopup();
        }

        function ShowConfigurationPopup(){
            ReloadConfiguration()
            document.getElementById("configurationPopup").style.display = "inline";
        }
        function SaveConfiguration(){
          SetConfiguration();
          //GetAvailableSettings();
          setTimeout(GetAvailableSettings, 100); 
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
          }else{
            document.getElementById("Configuration_Id").value   = '';
            document.getElementById("Configuration_Name").value = '';
            document.getElementById("Configuration_P").value    = '';
            document.getElementById("Configuration_I").value    = '';
            document.getElementById("Configuration_D").value    = '';
            document.getElementById("Configuration_StepsPerRevolution").value = '';
          }
        }
/**************************************************************************************/
/*      window on load       */
        window.onload = function() {
            var ctx = document.getElementById("myChart").getContext('2d');
            window.myLine = new Chart(ctx, ChartConfig);   

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

            GetActiveBrew()

            // var intervalID = setInterval(GetTemperature, 1000);
            // var intervalID = setInterval(GetServoAngle, 1000);
            // var intervalID = setInterval(GetOutput, 1000);
        };