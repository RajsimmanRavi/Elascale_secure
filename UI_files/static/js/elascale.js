/* Bunch of constants */
var config_params = ["cpu_up_lim", "mem_up_lim", "cpu_down_lim", "up_step", "down_step", "max_replica", "min_replica", "auto_scale"];


/* 
    Function to get only the different values between the default current values and newly insterted values.
    First argument tells us whether it's for micro or macro service. We can add approp. key such that server can understand it.
    Second argument tells the ID of the service so that we know which service was chosen.
    Third argument is the curr_default list
    Fourth argument is the newly inserted values list
*/
function get_diff(micro_or_macro, service, curr_list, new_list){

    var diff_dict = {};

    //Differentiate micro from macro
    diff_dict["service_type"] = micro_or_macro;

    //Add service 
    diff_dict["service"] = service;

    for (var i = 0; i < curr_list.length; i++){
    
	// If new value is not empty string
        if(new_list[i]){

	    // something changed
	    if(new_list[i] != curr_list[i]){
	        
                //The parameter string (eg. cpu_up_lim) that will be changed will be the key
                diff_dict[config_params[i]] = new_list[i];
	
            }
	
        }

    }

    return diff_dict;
}


/* 
   Function to fetch the current default values and/or newly inserted values. 
   I use this function for fetching both current values and any newly inserted values.
   I basically differentiate these two things based on the argument: "default" or "new".
   The other argument is the ID of the SUBMIT button pressed to identify which micro-service is   chosen.

*/
function get_vals_list(submit_id, default_or_new){
    
    var curr_list = [];
   
    for (var i = 0; i < config_params.length; i++){

	if (default_or_new == "default"){

	    var val = document.getElementById(submit_id+"_def_"+config_params[i]).innerHTML;
            curr_list.push(val);

	} else {

	    var val = document.getElementById(submit_id+"_"+config_params[i]).value;
            curr_list.push(val);
	}
    }

    return curr_list;
}


/* 
    Function that is called when SUBMIT button is pressed on micro (or macro)-services configuration page 

*/
function submit_change(service_type, self_id, ip_addr){
    
    var config_url = "wss://"+ip_addr+":8888/config";
    
    //Get the current default values of the micro-service config parameters
    var default_list = get_vals_list(self_id, "default");

    //Get inserted values of the micro-service config parameters
    var new_list = get_vals_list(self_id, "new");

    //Get the difference along with the affected config_param string as key
    var diff_dict = get_diff(service_type,self_id, default_list, new_list);
    
    //send dict to server 
  
    var ws = new WebSocket(config_url);
    
    ws.onopen = function() {
        ws.send(JSON.stringify(diff_dict));
    };

    ws.onmessage = function (evt) {
        var ret_data = evt.data;

        if(confirm(ret_data)){window.location.reload();}
    };
}
