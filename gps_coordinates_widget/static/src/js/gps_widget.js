odoo.define("gps_coordinates_widget.gps_location_widget", function (require) {
    "use strict";

    let fieldRegistry = require("web.field_registry");
    let FieldFloat = require("web.basic_fields").FieldFloat;
    const locationOptions = {
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 0,
    };

    let GpsCoordinates = FieldFloat.extend({

        _renderEdit: function () {
            this._super.apply(this, arguments);
            if(navigator && navigator.geolocation){
                let self = this;
                let gps_type = self.nodeOptions.gps_type;
                if(!(gps_type === undefined || gps_type === null)){
                    navigator.geolocation.getCurrentPosition(function(position){
                     if(!(self.$input === undefined || self.$input === null)){
                        let pos_val = 0;
                        if(gps_type == 'longitude'){
                            pos_val = position.coords.longitude;
                        }
                        else{
                            pos_val = position.coords.latitude;
                        }
                        console.log("Gps position: "+pos_val.toString());
                        self.$input.val(pos_val);
                        self._onInput();
                        self._onChange();
                        self.lastSetValue = 1; // last value should be different from the default field value that is 0. We put it to 1
                        self._setValue(pos_val.toString(), {forceChange:true});
                     }
                     else{
                        console.log("Error input gps field");
                     }
                }, function(error){console.log("Error gps browser api: "+ error.code + "/" + error.message);}, locationOptions);
                }
                else{
                    console.log("Erreur gps type");
                }
            }
        },
    });

    fieldRegistry.add("gps_coordinates", GpsCoordinates);

    return {
        GpsCoordinates: GpsCoordinates,
    };
});
