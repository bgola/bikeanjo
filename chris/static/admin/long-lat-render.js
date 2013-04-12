$(document).ready(function() {

    $('.field-geometry div textarea, .field-departure div textarea, .field-arrival div textarea').each(function(idx, elem) {
	    var mapid =  "map_canvas_" + idx;
	    var val = $(elem).val();
	    var marker_img = new google.maps.MarkerImage('/bike-anjo-marker-bigmap.png', null, null, new google.maps.Point(65, 65));
           
	    if (val) {
	    	    $(elem).parent().append("<div id='" + mapid +"' style='width:380px; height:200px; margin: 20px; margin-left: 105px;' ></div>");
		    val = val.substr(7);
		    var lng = val.split(' ')[0];
		    var lat = val.split(' ')[1];
		    lat = lat.substr(0, lat.length-1);
		    var latlng = new google.maps.LatLng(lat, lng);
		    var myOptions = {
		      zoom: 15,
		      center: latlng,
		      mapTypeId: google.maps.MapTypeId.ROADMAP
		    };
		    
		    var map = new google.maps.Map(document.getElementById(mapid),  myOptions);
		    var marker = new google.maps.Marker({
                    	map: map,
                        position: latlng,
                	icon: marker_img,
                	flat: true,
			draggable: false
            	     });
		    $(elem).hide();
	    }
    });
	 
});
