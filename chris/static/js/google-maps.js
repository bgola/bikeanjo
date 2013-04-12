
/*
Integration for Google Maps

based on django-google-maps
*/

function BikeAnjoMap(options) {

    var map_options = options;

    var geocoder = new google.maps.Geocoder();
    var map;
    var clusterer;
    var marker;
    var markers = {};
    var id = 0;
    var pixel_by_zoom = [2, 2, 2, 2.1020408163265306, 2.2040816326530612, 2.4081632653061224, 2.8333333333333334, 4.6666666666666667, 4.2733224222585924, 6.5359477124183005, 26.071895424836601, 50.315789473684212, 105.26315789473685, 200.0, 400.0, 833.3333333333334, 1666.6666666666667];
	    

    var self = {
        initialize: function(locations) {
	    var latlng = new google.maps.LatLng(-23.5000, -46.6167);
            var zoom = 7;
            
	    if(options.map_center) {
   	        geocoder.geocode({'address': options.map_center}, function(results, status) {
                    if (status == google.maps.GeocoderStatus.OK) {
                    latlng = results[0].geometry.location;
		    }
                });
	    }

	    map = new google.maps.Map(document.getElementById("map_canvas"), {
		    zoom: zoom,
		    center: latlng,
		    mapTypeId: google.maps.MapTypeId.ROADMAP,
		    minZoom: options.minZoom,
		    maxZoom: options.maxZoom
	    	});

	    if (options.clusterer) {
		    clusterer = new MarkerClusterer(map, [], {gridSize: 30});
	    }

       	    if (locations.length > 0) {
		var latlngbounds = new google.maps.LatLngBounds( );
  	        for (var i=0; i<locations.length; i++) { 
		    var latlng_bounds = new google.maps.LatLng(locations[i].lat, locations[i].lng);
                    self.setMarker(latlng_bounds);
		    self.saveMarker(locations[i].label);
		    latlngbounds.extend(latlng_bounds);
	        }
                map.fitBounds(latlngbounds);
		var listener = google.maps.event.addListener(map, "idle", function() { 
			  map.setZoom(map.getZoom()-1); 
			    google.maps.event.removeListener(listener); 
		});
	    }

            if (map_options.resize_icon) {
		    google.maps.event.addListener(map, 'zoom_changed', function() {
			    var zoom = map.getZoom();
    			    for(m in markers) {
				    var old_icon = markers[m].getIcon();
				    markers[m].setIcon(new google.maps.MarkerImage(
					    old_icon.url,
					    null,
					    null,
					    new google.maps.Point(pixel_by_zoom[zoom]/2, pixel_by_zoom[zoom]/2),
					    new google.maps.Size(pixel_by_zoom[zoom], pixel_by_zoom[zoom])));
			    }
		    });
	    }

	    $("#address").change(function() {self.codeAddress('#address');});
	    $("#id_departure_label").change(function() {self.codeAddress('#id_departure_label');});
	    $("#id_arrival_label").change(function() {self.codeAddress('#id_arrival_label');});

	    $("#id_departure_label").keydown(function(e) {
		    if (e.keyCode == 13) {
			    e.preventDefault()
		            self.codeAddress("#id_departure_label", function() { $("#id_departure_label").focus();});
		    }
	    });
	    $("#id_arrival_label").keydown(function(e) {
		    if (e.keyCode == 13) {
			    e.preventDefault()
		            self.codeAddress("#id_arrival_label", function() { $("#id_arrival_label").focus();});
		    }
	    });
        $("#address").keydown(function(e) {
		    if (e.keyCode == 13) {
			    e.preventDefault()
		            self.codeAddress("#address", function() { $("#address").focus();});
		    }
	    });
        self.cleanInput('#address');
	    self.cleanInput('#id_departure_label');
	    self.cleanInput('#id_arrival_label');
        },

        codeAddress: function(input_selector, cb) {
            if (!input_selector) 
                input_selector = '#address';

            var address = $(input_selector).val();
            geocoder.geocode({'address': address}, function(results, status) {
                if (status == google.maps.GeocoderStatus.OK) {
                    var latlng = results[0].geometry.location;
                    map.setCenter(latlng);
                    map.setZoom(13);

                    self.setMarker(latlng, input_selector);
            
                    if (cb)
                        cb();
                } else {
                    alert("Geocode was not successful for the following reason: " + status);
                }
            });
        },

        setMarker: function(latlng, marker_name) {
            if (marker && markers[marker_name]) {
                self.updateMarker(latlng, marker_name);
            } else {
                self.addMarker({'latlng': latlng, 'draggable': map_options.draggable, 'name': marker_name});
            }
        },

	cleanInput: function(input_selector) {
			$(input_selector).val("Ex: Rua Cristiano Viana, 1023 - São Paulo ou 05411-000");
			$(input_selector).css("color", "#999");
			$(input_selector).focus(function() { 
				$(input_selector).unbind("focus");
				$(input_selector).val("");
				$(input_selector).css("color", "#000");
			});
	},

	saveMarker: function(label) {
		if(marker) {
			if (!label) 
			label = $("#address").val();
			marker.setTitle(label);
			marker = undefined;
			$("#locations").append("<li id='marker_" + id + "'><a href='javascript:bmap.removeMarker(" + id + ")'>&times;</a> <a class='gmaps-label' href='javascript:bmap.showMarker(" + id +")'>" + label + "</a></li>");
			self.cleanInput('#address');
    		}
	},
	
	removeMarker: function(marker_id) {
		$("li#marker_" + marker_id).hide();
		markers[marker_id].setMap(null);
		delete markers[marker_id];
		self.cleanInput('#address');
	},
	
	showMarker: function(marker_id) {
		map.setCenter(markers[marker_id].getPosition());
                map.setZoom(13);
	},


        addMarker: function(Options) {
	    id++;
	    marker_img = new google.maps.MarkerImage(map_options.icon, null, null, new google.maps.Point(map_options.icon_center_x, map_options.icon_center_y));
	    var marker_opts =  {
                position: Options.latlng,
	    	icon: marker_img,
	        flat: true
            };
	    if (!options.clusterer) {
		    marker_opts['map'] = map;
	    }
            marker = new google.maps.Marker(marker_opts);
	    marker.setDraggable(Options.draggable);
	    markers[id] = marker;
	    markers[Options.name] = marker;
	    if (options.clusterer) {
		    clusterer.addMarker(marker);
	    }
        },

	getMarkers: function() {
		return markers;
	},

        updateMarker: function(latlng, marker_name) {
            markers[marker_name].setPosition(latlng);
        },

	exportMarkers: function() {
	    var markers_export = [];
	    for(var m in markers) {
		// checks if m is a number
		if (! isNaN (m-0) && m != null) {
	        	markers_export.push({lat: markers[m].position.lat(), 
		                     lng: markers[m].position.lng(),
		                     label: $("li#marker_" + m + " a.gmaps-label").text()})
		}
	    }
	    return JSON.stringify(markers_export);
	}
    }
    return self;
}

