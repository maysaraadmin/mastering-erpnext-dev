# Chapter 35: External Integrations and Web Services

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Integrating Google Maps** to replace OpenStreetMap in Frappe applications
- **Implementing geolocation** with Nominatim API for address validation
- **Building webhook systems** for real-time data synchronization
- **Creating payment gateway integrations** with Stripe, PayPal, and others
- **Developing email/SMS integrations** with SendGrid, Twilio, and AWS SES
- **Implementing social media integrations** with Facebook, Twitter, LinkedIn
- **Building REST API integrations** with third-party services
- **Managing API authentication** and security for external services

## 📚 Chapter Topics

### 35.1 Google Maps Integration

**Replacing OpenStreetMap with Google Maps**

This documentation provides a clean and structured explanation of how to replace OpenStreetMap with Google Maps in a Frappe-based application. The example demonstrates integrating Google Maps for geolocation visualization and updating the map dynamically based on latitude and longitude values.

#### Backend Configuration

**Fetching the Google Maps API Key**

To ensure security, the Google Maps API key is stored encrypted in the system settings. A custom method retrieves the decrypted key.

```python
# your_app/utils/google_maps.py
import frappe
from frappe.utils.password import get_decrypted_password

@frappe.whitelist()
def get_google_map_api_key():
    """
    Retrieves the decrypted Google Maps API key from the system settings.
    """
    return get_decrypted_password("System Settings", "System Settings", "google_map_api_key")

@frappe.whitelist()
def geocode_address(address):
    """
    Convert address to latitude and longitude using Google Maps Geocoding API
    """
    api_key = get_google_map_api_key()
    
    if not api_key:
        frappe.throw("Google Maps API key not configured")
    
    import requests
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
        else:
            frappe.throw(f"Geocoding failed: {data.get('status', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Geocoding request failed: {str(e)}")

@frappe.whitelist()
def reverse_geocode(lat, lng):
    """
    Convert latitude and longitude to address using Google Maps Reverse Geocoding API
    """
    api_key = get_google_map_api_key()
    
    if not api_key:
        frappe.throw("Google Maps API key not configured")
    
    import requests
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'latlng': f"{lat},{lng}",
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            return {
                'address': data['results'][0]['formatted_address'],
                'address_components': data['results'][0]['address_components']
            }
        else:
            frappe.throw(f"Reverse geocoding failed: {data.get('status', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Reverse geocoding request failed: {str(e)}")
```

#### Frontend Integration

**Custom Google Maps Field**

```javascript
// your_app/public/js/google_maps_field.js
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        // Initialize Google Maps field
        initialize_google_maps_field(frm);
    }
});

function initialize_google_maps_field(frm) {
    let map_field = frm.fields_dict['google_map'];
    if (!map_field) return;
    
    // Create map container
    let $wrapper = map_field.$wrapper;
    $wrapper.empty();
    
    let $map_container = $(`
        <div class="google-maps-wrapper">
            <div id="google_map_canvas" style="height: 400px; width: 100%; border: 1px solid #ddd;"></div>
            <div class="map-controls mt-2">
                <div class="row">
                    <div class="col-md-6">
                        <button class="btn btn-sm btn-primary" id="get_location_btn">
                            <i class="fa fa-location-arrow"></i> Get Current Location
                        </button>
                        <button class="btn btn-sm btn-default" id="geocode_btn">
                            <i class="fa fa-search"></i> Geocode Address
                        </button>
                    </div>
                    <div class="col-md-6 text-right">
                        <button class="btn btn-sm btn-default" id="clear_markers_btn">
                            <i class="fa fa-trash"></i> Clear Markers
                        </button>
                        <button class="btn btn-sm btn-default" id="reset_view_btn">
                            <i class="fa fa-compress"></i> Reset View
                        </button>
                    </div>
                </div>
            </div>
            <div class="map-info mt-2">
                <small class="text-muted">
                    <span id="map_info_text">Click on the map to set location</span>
                </small>
            </div>
        </div>
    `);
    
    $wrapper.append($map_container);
    
    // Initialize Google Maps
    initialize_map(frm);
    
    // Bind control events
    bind_map_controls(frm);
}

function initialize_map(frm) {
    // Load Google Maps API
    if (!window.google || !window.google.maps) {
        load_google_maps_api().then(function() {
            create_map_instance(frm);
        });
    } else {
        create_map_instance(frm);
    }
}

function load_google_maps_api() {
    return new Promise(function(resolve, reject) {
        frappe.call({
            method: 'your_app.utils.google_maps.get_google_map_api_key',
            callback: function(response) {
                let api_key = response.message;
                
                if (!api_key) {
                    frappe.msgprint('Google Maps API key not configured');
                    reject();
                    return;
                }
                
                // Load Google Maps script
                let script = document.createElement('script');
                script.src = `https://maps.googleapis.com/maps/api/js?key=${api_key}&libraries=places&callback=initMaps`;
                script.async = true;
                script.defer = true;
                
                window.initMaps = function() {
                    resolve();
                };
                
                script.onerror = function() {
                    reject();
                };
                
                document.head.appendChild(script);
            }
        });
    });
}

function create_map_instance(frm) {
    let mapOptions = {
        center: {lat: 0, lng: 0},
        zoom: 2,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
            {
                featureType: "poi.business",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    };
    
    frm.google_map = new google.maps.Map(document.getElementById('google_map_canvas'), mapOptions);
    frm.google_markers = [];
    
    // Add click event to map
    frm.google_map.addListener('click', function(event) {
        add_marker(frm, event.latLng);
    });
    
    // Set initial location if coordinates exist
    if (frm.doc.latitude && frm.doc.longitude) {
        let position = {lat: parseFloat(frm.doc.latitude), lng: parseFloat(frm.doc.longitude)};
        frm.google_map.setCenter(position);
        frm.google_map.setZoom(15);
        add_marker(frm, position);
    }
    
    // Initialize autocomplete for address field
    initialize_address_autocomplete(frm);
}

function initialize_address_autocomplete(frm) {
    let address_field = frm.fields_dict['address'];
    if (!address_field) return;
    
    let autocomplete = new google.maps.places.Autocomplete(address_field.$input[0]);
    
    autocomplete.addListener('place_changed', function() {
        let place = autocomplete.getPlace();
        
        if (place.geometry) {
            let position = place.geometry.location;
            frm.google_map.setCenter(position);
            frm.google_map.setZoom(15);
            add_marker(frm, position);
            
            // Update coordinates
            frm.set_value('latitude', position.lat());
            frm.set_value('longitude', position.lng());
            
            update_map_info(frm, place.formatted_address);
        }
    });
}

function add_marker(frm, position) {
    // Clear existing markers
    clear_markers(frm);
    
    let marker = new google.maps.Marker({
        position: position,
        map: frm.google_map,
        draggable: true,
        animation: google.maps.Animation.DROP
    });
    
    // Add drag event
    marker.addListener('dragend', function(event) {
        let new_position = event.latLng;
        frm.set_value('latitude', new_position.lat());
        frm.set_value('longitude', new_position.lng());
        
        // Get address from coordinates
        reverse_geocode(frm, new_position.lat(), new_position.lng());
    });
    
    frm.google_markers.push(marker);
    
    // Update coordinates
    frm.set_value('latitude', position.lat());
    frm.set_value('longitude', position.lng());
    
    // Get address from coordinates
    reverse_geocode(frm, position.lat(), position.lng());
}

function clear_markers(frm) {
    frm.google_markers.forEach(function(marker) {
        marker.setMap(null);
    });
    frm.google_markers = [];
}

function bind_map_controls(frm) {
    // Get current location
    $('#get_location_btn').on('click', function() {
        get_current_location(frm);
    });
    
    // Geocode address
    $('#geocode_btn').on('click', function() {
        geocode_address(frm);
    });
    
    // Clear markers
    $('#clear_markers_btn').on('click', function() {
        clear_markers(frm);
        frm.set_value('latitude', '');
        frm.set_value('longitude', '');
        update_map_info(frm, 'Click on the map to set location');
    });
    
    // Reset view
    $('#reset_view_btn').on('click', function() {
        if (frm.google_markers.length > 0) {
            frm.google_map.setCenter(frm.google_markers[0].getPosition());
            frm.google_map.setZoom(15);
        } else {
            frm.google_map.setCenter({lat: 0, lng: 0});
            frm.google_map.setZoom(2);
        }
    });
}

function get_current_location(frm) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                let lat = position.coords.latitude;
                let lng = position.coords.longitude;
                let pos = {lat: lat, lng: lng};
                
                frm.google_map.setCenter(pos);
                frm.google_map.setZoom(15);
                add_marker(frm, pos);
                
                update_map_info(frm, 'Current location set successfully');
            },
            function(error) {
                frappe.msgprint('Unable to get current location: ' + error.message);
            }
        );
    } else {
        frappe.msgprint('Geolocation is not supported by this browser');
    }
}

function geocode_address(frm) {
    let address = frm.doc.address || '';
    
    if (!address) {
        frappe.msgprint('Please enter an address first');
        return;
    }
    
    frappe.call({
        method: 'your_app.utils.google_maps.geocode_address',
        args: {
            address: address
        },
        callback: function(response) {
            if (response.message) {
                let result = response.message;
                let position = {lat: result.latitude, lng: result.longitude};
                
                frm.google_map.setCenter(position);
                frm.google_map.setZoom(15);
                add_marker(frm, position);
                
                update_map_info(frm, result.formatted_address);
            }
        }
    });
}

function reverse_geocode(frm, lat, lng) {
    frappe.call({
        method: 'your_app.utils.google_maps.reverse_geocode',
        args: {
            lat: lat,
            lng: lng
        },
        callback: function(response) {
            if (response.message) {
                let address = response.message.address;
                update_map_info(frm, address);
                
                // Update address field if it's empty
                if (!frm.doc.address) {
                    frm.set_value('address', address);
                }
            }
        }
    });
}

function update_map_info(frm, message) {
    $('#map_info_text').text(message);
}
```

**Advanced Google Maps Features**

```javascript
// Advanced map features
function add_advanced_map_features(frm) {
    // Add drawing tools
    add_drawing_tools(frm);
    
    // Add heatmap layer
    add_heatmap_layer(frm);
    
    // Add directions service
    add_directions_service(frm);
    
    // Add custom controls
    add_custom_controls(frm);
}

function add_drawing_tools(frm) {
    let drawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: google.maps.drawing.OverlayType.MARKER,
        drawingControl: true,
        drawingControlOptions: {
            position: google.maps.ControlPosition.TOP_CENTER,
            drawingModes: [
                google.maps.drawing.OverlayType.MARKER,
                google.maps.drawing.OverlayType.CIRCLE,
                google.maps.drawing.OverlayType.POLYGON,
                google.maps.drawing.OverlayType.RECTANGLE
            ]
        },
        markerOptions: {
            icon: 'https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png'
        }
    });
    
    drawingManager.setMap(frm.google_map);
    
    google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
        if (event.type === google.maps.drawing.OverlayType.MARKER) {
            let marker = event.overlay;
            save_marker_location(frm, marker.getPosition());
        }
    });
}

function add_heatmap_layer(frm) {
    // Example: Show customer density heatmap
    frappe.call({
        method: 'your_app.api.get_customer_locations',
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                let heatmapData = response.message.map(function(location) {
                    return new google.maps.LatLng(location.latitude, location.longitude);
                });
                
                let heatmap = new google.maps.visualization.HeatmapLayer({
                    data: heatmapData,
                    map: frm.google_map,
                    radius: 50
                });
            }
        }
    });
}

function add_directions_service(frm) {
    let directionsService = new google.maps.DirectionsService();
    let directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(frm.google_map);
    
    // Add route calculation
    frm.add_custom_button('Calculate Route', function() {
        calculate_route(frm, directionsService, directionsRenderer);
    });
}

function calculate_route(frm, directionsService, directionsRenderer) {
    let start = frm.doc.start_address;
    let end = frm.doc.end_address;
    
    if (!start || !end) {
        frappe.msgprint('Please provide both start and end addresses');
        return;
    }
    
    let request = {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING
    };
    
    directionsService.route(request, function(result, status) {
        if (status === google.maps.DirectionsStatus.OK) {
            directionsRenderer.setDirections(result);
            
            // Calculate distance and duration
            let route = result.routes[0];
            let distance = route.legs[0].distance.text;
            let duration = route.legs[0].duration.text;
            
            frm.set_value('distance', distance);
            frm.set_value('duration', duration);
            
            update_map_info(frm, `Distance: ${distance}, Duration: ${duration}`);
        } else {
            frappe.msgprint('Directions request failed: ' + status);
        }
    });
}
```

### 35.2 Geolocation with Nominatim API

**Alternative Geocoding Service**

```python
# your_app/utils/geolocation.py
import frappe
import requests
from urllib.parse import quote

class NominatimGeocoder:
    """Geocoding service using OpenStreetMap Nominatim API"""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    
    @staticmethod
    def geocode(address, limit=1):
        """
        Convert address to coordinates using Nominatim API
        
        Args:
            address (str): Address to geocode
            limit (int): Number of results to return
            
        Returns:
            dict: Geocoding results with latitude, longitude, and address details
        """
        params = {
            'q': address,
            'format': 'json',
            'limit': limit,
            'addressdetails': 1,
            'countrycodes': '',  # Specify country codes if needed
        }
        
        try:
            response = requests.get(NominatimGeocoder.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                return None
            
            # Return first result
            result = results[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name'],
                'address': result.get('address', {}),
                'importance': result.get('importance', 0),
                'osm_type': result.get('osm_type'),
                'osm_id': result.get('osm_id')
            }
            
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Nominatim geocoding failed: {str(e)}", "Geocoding Error")
            return None
    
    @staticmethod
    def reverse_geocode(lat, lon):
        """
        Convert coordinates to address using Nominatim API
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Reverse geocoding results with address details
        """
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18
        }
        
        try:
            response = requests.get(NominatimGeocoder.REVERSE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                return None
            
            return {
                'display_name': result['display_name'],
                'address': result.get('address', {}),
                'osm_type': result.get('osm_type'),
                'osm_id': result.get('osm_id'),
                'place_id': result.get('place_id')
            }
            
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Nominatim reverse geocoding failed: {str(e)}", "Geocoding Error")
            return None

@frappe.whitelist()
def get_coordinates_from_address(address):
    """Get coordinates from address using Nominatim"""
    geocoder = NominatimGeocoder()
    result = geocoder.geocode(address)
    
    if result:
        return {
            'success': True,
            'latitude': result['latitude'],
            'longitude': result['longitude'],
            'address': result['display_name']
        }
    else:
        return {
            'success': False,
            'message': 'Address not found'
        }

@frappe.whitelist()
def get_address_from_coordinates(lat, lon):
    """Get address from coordinates using Nominatim"""
    geocoder = NominatimGeocoder()
    result = geocoder.reverse_geocode(lat, lon)
    
    if result:
        return {
            'success': True,
            'address': result['display_name'],
            'address_components': result['address']
        }
    else:
        return {
            'success': False,
            'message': 'Address not found'
        }

@frappe.whitelist()
def validate_address(address):
    """Validate and standardize address"""
    geocoder = NominatimGeocoder()
    result = geocoder.geocode(address, limit=5)
    
    if result:
        return {
            'success': True,
            'suggestions': [
                {
                    'display_name': r['display_name'],
                    'latitude': r['latitude'],
                    'longitude': r['longitude'],
                    'address': r['address']
                }
                for r in result[:5]
            ]
        }
    else:
        return {
            'success': False,
            'message': 'Address validation failed'
        }
```

**Frontend Nominatim Integration**

```javascript
// your_app/public/js/nominatim_field.js
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        initialize_nominatim_field(frm);
    }
});

function initialize_nominatim_field(frm) {
    let address_field = frm.fields_dict['address'];
    if (!address_field) return;
    
    // Add address validation button
    address_field.$wrapper.find('.control-input').append(`
        <button class="btn btn-xs btn-default" type="button" id="validate_address_btn">
            <i class="fa fa-check"></i> Validate
        </button>
    `);
    
    // Bind validation event
    $('#validate_address_btn').on('click', function() {
        validate_address_with_nominatim(frm);
    });
    
    // Add real-time validation with debouncing
    let validate_timeout;
    address_field.$input.on('input', function() {
        clearTimeout(validate_timeout);
        validate_timeout = setTimeout(function() {
            if (address_field.get_value().length > 5) {
                validate_address_with_nominatim(frm, false);
            }
        }, 1000);
    });
}

function validate_address_with_nominatim(frm, show_suggestions = true) {
    let address = frm.doc.address || '';
    
    if (!address || address.length < 5) {
        return;
    }
    
    frappe.call({
        method: 'your_app.utils.geolocation.validate_address',
        args: {
            address: address
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                handle_address_validation_result(frm, response.message.suggestions, show_suggestions);
            } else {
                show_address_validation_error(frm, response.message.message || 'Validation failed');
            }
        }
    });
}

function handle_address_validation_result(frm, suggestions, show_dialog) {
    if (!show_dialog || suggestions.length === 1) {
        // Auto-select single suggestion
        let suggestion = suggestions[0];
        update_coordinates_from_suggestion(frm, suggestion);
        show_address_validation_success(frm, 'Address validated successfully');
    } else {
        // Show suggestions dialog
        show_address_suggestions_dialog(frm, suggestions);
    }
}

function show_address_suggestions_dialog(frm, suggestions) {
    let dialog = new frappe.ui.Dialog({
        title: __('Address Suggestions'),
        size: 'large',
        fields: [
            {
                fieldname: 'suggestions',
                fieldtype: 'HTML',
                options: get_suggestions_html(suggestions)
            }
        ]
    });
    
    dialog.show();
    
    // Bind click events to suggestions
    dialog.$wrapper.find('.address-suggestion').on('click', function() {
        let suggestion_data = $(this).data('suggestion');
        update_coordinates_from_suggestion(frm, suggestion_data);
        dialog.hide();
    });
}

function get_suggestions_html(suggestions) {
    let html = '<div class="address-suggestions">';
    
    suggestions.forEach(function(suggestion, index) {
        html += `
            <div class="address-suggestion p-3 border-bottom cursor-pointer" 
                 data-suggestion='${JSON.stringify(suggestion)}'>
                <div class="suggestion-title font-weight-bold">
                    ${suggestion.display_name}
                </div>
                <div class="suggestion-coords text-muted small">
                    Lat: ${suggestion.latitude}, Lng: ${suggestion.longitude}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function update_coordinates_from_suggestion(frm, suggestion) {
    frm.set_value('latitude', suggestion.latitude);
    frm.set_value('longitude', suggestion.longitude);
    frm.set_value('address', suggestion.display_name);
    
    // Update map if available
    if (frm.google_map) {
        let position = {lat: suggestion.latitude, lng: suggestion.longitude};
        frm.google_map.setCenter(position);
        frm.google_map.setZoom(15);
        add_marker(frm, position);
    }
}

function show_address_validation_success(frm, message) {
    frm.dashboard.clear_comment();
    frm.dashboard.add_comment(message, 'green');
    
    // Remove validation error styling
    frm.fields_dict.address.$wrapper.removeClass('has-error');
}

function show_address_validation_error(frm, message) {
    frm.dashboard.clear_comment();
    frm.dashboard.add_comment(message, 'red');
    
    // Add validation error styling
    frm.fields_dict.address.$wrapper.addClass('has-error');
}
```

### 35.3 Webhook Integration System

**Webhook Theory and Implementation**

Webhooks are automated messages sent from apps when something happens. They have a message—or payload—and are sent to a unique URL—essentially the app's phone number or address.

**Webhook Architecture**

```python
# your_app/hooks.py
# Add webhook hooks
webhook_doctypes = ["Sales Order", "Customer", "Invoice"]
webhook_events = {
    "on_update": ["Sales Order", "Customer"],
    "on_submit": ["Sales Order", "Invoice"],
    "on_cancel": ["Sales Order", "Invoice"]
}
```

**Webhook Management System**

```python
# your_app/doctype/webhook/webhook.py
import frappe
import json
import requests
from datetime import datetime
import hashlib
import hmac

class WebhookManager:
    """Manages webhook creation, processing, and delivery"""
    
    @staticmethod
    def create_webhook(doctype, events, url, secret_key=None, headers=None):
        """Create a new webhook configuration"""
        webhook = frappe.get_doc({
            "doctype": "Webhook",
            "webhook_doctype": doctype,
            "webhook_events": "\n".join(events),
            "webhook_url": url,
            "secret_key": secret_key or frappe.utils.generate_hash(length=32),
            "enable_security": 1 if secret_key else 0,
            "request_headers": headers or {}
        })
        webhook.insert()
        return webhook
    
    @staticmethod
    def trigger_webhook(doc, event):
        """Trigger webhook for document event"""
        webhooks = frappe.get_all("Webhook", 
            filters={
                "webhook_doctype": doc.doctype,
                "enabled": 1
            }
        )
        
        for webhook_name in webhooks:
            webhook = frappe.get_doc("Webhook", webhook_name.name)
            
            if event in webhook.webhook_events_list:
                WebhookManager.send_webhook(webhook, doc, event)
    
    @staticmethod
    def send_webhook(webhook, doc, event):
        """Send webhook payload"""
        try:
            # Prepare payload
            payload = WebhookManager.prepare_payload(doc, event)
            
            # Add signature if security is enabled
            headers = webhook.request_headers or {}
            if webhook.enable_security:
                signature = WebhookManager.generate_signature(payload, webhook.secret_key)
                headers['X-Hub-Signature'] = f"sha256={signature}"
            
            # Add webhook headers
            headers.update({
                'Content-Type': 'application/json',
                'X-Frappe-Event': event,
                'X-Frappe-Doctype': doc.doctype,
                'X-Frappe-Docname': doc.name,
                'X-Webhook-ID': webhook.name
            })
            
            # Send webhook
            response = requests.post(
                webhook.webhook_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            # Log webhook attempt
            WebhookManager.log_webhook_attempt(webhook, doc, event, response)
            
            return response.status_code == 200
            
        except Exception as e:
            # Log failed webhook
            WebhookManager.log_webhook_attempt(webhook, doc, event, None, str(e))
            return False
    
    @staticmethod
    def prepare_payload(doc, event):
        """Prepare webhook payload"""
        payload = {
            "event": event,
            "doctype": doc.doctype,
            "docname": doc.name,
            "timestamp": datetime.now().isoformat(),
            "data": doc.as_dict()
        }
        
        # Add specific event data
        if event == "on_submit":
            payload["submitted_by"] = doc.owner
            payload["submitted_on"] = doc.modified
        elif event == "on_cancel":
            payload["cancelled_by"] = doc.owner
            payload["cancelled_on"] = doc.modified
        
        return payload
    
    @staticmethod
    def generate_signature(payload, secret_key):
        """Generate HMAC signature for webhook"""
        payload_string = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(payload, signature, secret_key):
        """Verify webhook signature"""
        expected_signature = WebhookManager.generate_signature(payload, secret_key)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def log_webhook_attempt(webhook, doc, event, response, error=None):
        """Log webhook delivery attempt"""
        log_entry = frappe.get_doc({
            "doctype": "Webhook Log",
            "webhook": webhook.name,
            "reference_doctype": doc.doctype,
            "reference_docname": doc.name,
            "event": event,
            "status": "Success" if response and response.status_code == 200 else "Failed",
            "response_code": response.status_code if response else None,
            "response_data": response.text if response else None,
            "error_message": error,
            "creation": datetime.now()
        })
        log_entry.insert(ignore_permissions=True)

# Webhook event handlers
def on_doctype_update(doc, method):
    """Trigger webhook on document update"""
    WebhookManager.trigger_webhook(doc, "on_update")

def on_doctype_submit(doc, method):
    """Trigger webhook on document submit"""
    WebhookManager.trigger_webhook(doc, "on_submit")

def on_doctype_cancel(doc, method):
    """Trigger webhook on document cancel"""
    WebhookManager.trigger_webhook(doc, "on_cancel")

# Apply webhook hooks dynamically
def apply_webhook_hooks():
    """Apply webhook hooks to configured doctypes"""
    webhooks = frappe.get_all("Webhook", {"enabled": 1})
    
    for webhook_name in webhooks:
        webhook = frappe.get_doc("Webhook", webhook_name.name)
        doctype = webhook.webhook_doctype
        
        # Add hooks for this doctype
        if "on_update" in webhook.webhook_events_list:
            frappe.get_doc(doctype).on_update = on_doctype_update
        
        if "on_submit" in webhook.webhook_events_list:
            frappe.get_doc(doctype).on_submit = on_doctype_submit
        
        if "on_cancel" in webhook.webhook_events_list:
            frappe.get_doc(doctype).on_cancel = on_doctype_cancel
```

**Webhook Processing API**

```python
# your_app/api/webhooks.py
import frappe
import json
from frappe.utils.password import get_decrypted_password

@frappe.whitelist(allow_guest=True)
def process_webhook(webhook_id, event, doctype, docname, signature=None):
    """Process incoming webhook"""
    try:
        # Get webhook configuration
        webhook = frappe.get_doc("Webhook", webhook_id)
        
        if not webhook.enabled:
            frappe.throw("Webhook is disabled")
        
        # Verify signature if security is enabled
        if webhook.enable_security:
            if not signature:
                frappe.throw("Missing signature")
            
            # Get request body
            request_data = frappe.request.get_data()
            payload = json.loads(request_data.decode('utf-8'))
            
            if not WebhookManager.verify_signature(payload, signature, webhook.secret_key):
                frappe.throw("Invalid signature")
        
        # Get the document
        doc = frappe.get_doc(doctype, docname)
        
        # Process webhook based on event
        result = process_webhook_event(webhook, doc, event)
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "result": result
        }
        
    except Exception as e:
        frappe.log_error(f"Webhook processing failed: {str(e)}", "Webhook Error")
        return {
            "success": False,
            "message": str(e)
        }

def process_webhook_event(webhook, doc, event):
    """Process specific webhook event"""
    if event == "on_update":
        return handle_update_event(webhook, doc)
    elif event == "on_submit":
        return handle_submit_event(webhook, doc)
    elif event == "on_cancel":
        return handle_cancel_event(webhook, doc)
    else:
        frappe.throw(f"Unknown event: {event}")

def handle_update_event(webhook, doc):
    """Handle document update event"""
    # Custom logic for update events
    if doc.doctype == "Sales Order":
        # Update external system
        update_external_sales_order(doc)
        return {"status": "updated", "external_id": doc.external_id}
    
    return {"status": "processed"}

def handle_submit_event(webhook, doc):
    """Handle document submit event"""
    # Custom logic for submit events
    if doc.doctype == "Sales Order":
        # Create external order
        external_id = create_external_order(doc)
        doc.external_id = external_id
        doc.save(ignore_permissions=True)
        return {"status": "submitted", "external_id": external_id}
    
    return {"status": "processed"}

def handle_cancel_event(webhook, doc):
    """Handle document cancel event"""
    # Custom logic for cancel events
    if doc.doctype == "Sales Order":
        # Cancel external order
        cancel_external_order(doc.external_id)
        return {"status": "cancelled", "external_id": doc.external_id}
    
    return {"status": "processed"}

def update_external_sales_order(doc):
    """Update sales order in external system"""
    # Implementation for external system integration
    pass

def create_external_order(doc):
    """Create order in external system"""
    # Implementation for external system integration
    return "EXT-" + doc.name

def cancel_external_order(external_id):
    """Cancel order in external system"""
    # Implementation for external system integration
    pass
```

**Webhook Testing and Debugging**

```python
# your_app/utils/webhook_tester.py
import frappe
import json
import requests
from datetime import datetime

class WebhookTester:
    """Utility for testing webhooks"""
    
    @staticmethod
    def test_webhook(webhook_name, test_data=None):
        """Test webhook with sample data"""
        webhook = frappe.get_doc("Webhook", webhook_name)
        
        if not webhook.enabled:
            return {"success": False, "message": "Webhook is disabled"}
        
        # Create test document
        test_doc = create_test_document(webhook.webhook_doctype, test_data)
        
        # Test webhook delivery
        result = WebhookManager.send_webhook(webhook, test_doc, "on_update")
        
        return {
            "success": result,
            "webhook": webhook_name,
            "test_doc": test_doc.name,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_test_document(doctype, test_data=None):
        """Create a test document for webhook testing"""
        default_data = {
            "name": f"TEST-{doctype}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "docstatus": 0,
            "owner": "Administrator",
            "creation": datetime.now()
        }
        
        if test_data:
            default_data.update(test_data)
        
        # Create test document
        test_doc = frappe.get_doc({
            "doctype": doctype,
            **default_data
        })
        test_doc.insert(ignore_permissions=True)
        
        return test_doc
    
    @staticmethod
    def simulate_webhook_event(webhook_name, event, docname):
        """Simulate webhook event for existing document"""
        webhook = frappe.get_doc("Webhook", webhook_name)
        doc = frappe.get_doc(webhook.webhook_doctype, docname)
        
        result = WebhookManager.send_webhook(webhook, doc, event)
        
        return {
            "success": result,
            "webhook": webhook_name,
            "event": event,
            "docname": docname,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_webhook_logs(webhook_name, limit=50):
        """Get recent webhook logs"""
        logs = frappe.get_all("Webhook Log",
            filters={"webhook": webhook_name},
            fields=["name", "event", "status", "response_code", "creation", "error_message"],
            order_by="creation desc",
            limit=limit
        )
        
        return logs

@frappe.whitelist()
def test_webhook_delivery(webhook_name):
    """Test webhook delivery"""
    tester = WebhookTester()
    result = tester.test_webhook(webhook_name)
    
    return result

@frappe.whitelist()
def simulate_webhook_event(webhook_name, event, docname):
    """Simulate webhook event"""
    tester = WebhookTester()
    result = tester.simulate_webhook_event(webhook_name, event, docname)
    
    return result

@frappe.whitelist()
def get_webhook_logs(webhook_name):
    """Get webhook logs"""
    tester = WebhookTester()
    logs = tester.get_webhook_logs(webhook_name)
    
    return logs
```

---

## 🎯 **Integration Best Practices Summary**

### **Security Considerations**
- **API Key Management**: Store API keys encrypted in system settings
- **Request Validation**: Validate all incoming webhook requests
- **Rate Limiting**: Implement rate limiting for external API calls
- **Error Handling**: Handle API failures gracefully without exposing sensitive data

### **Performance Optimization**
- **Caching**: Cache geocoding results to reduce API calls
- **Batch Processing**: Process multiple webhooks in batches
- **Async Processing**: Use background jobs for long-running integrations
- **Retry Logic**: Implement exponential backoff for failed requests

### **Monitoring and Debugging**
- **Logging**: Log all integration requests and responses
- **Health Checks**: Monitor external service availability
- **Error Tracking**: Track and analyze integration failures
- **Performance Metrics**: Monitor API response times and success rates

### **Data Management**
- **Data Validation**: Validate data before sending to external services
- **Data Mapping**: Map Frappe fields to external service fields
- **Data Synchronization**: Keep data synchronized across systems
- **Backup and Recovery**: Maintain backup of integration data

---

**💡 Pro Tip**: Always test integrations in a development environment before deploying to production. Use sandbox/test accounts provided by external services to avoid affecting real data. Monitor integration performance and set up alerts for failures.


---

## 📌 Addendum: Webhooks, ngrok, Integration Requests, and SPAs

### Webhook Theory

**API vs Webhook:**

| | API | Webhook |
|---|---|---|
| Direction | Pull (client requests) | Push (server sends) |
| Trigger | Manual request | Event occurrence |
| Communication | Two-way | One-way |
| Use case | "Give me data now" | "Notify me when X happens" |

A webhook is an automated HTTP POST sent from App A to App B when an event occurs. App B doesn't need to ask — it just receives.

**How webhooks work:**

1. App B exposes an endpoint (e.g., `/api/webhooks/order`)
2. App A is configured with App B's URL and the triggering event
3. When the event occurs, App A POSTs data to App B's URL
4. App B processes the data and returns `200 OK`

**Frappe as webhook receiver:**

```python
@frappe.whitelist(allow_guest=True)
def receive_webhook():
    data = frappe.request.get_json()
    # Validate signature if needed
    # Process data
    frappe.get_doc({
        "doctype": "Integration Request",
        "integration_request_service": "MyWebhook",
        "data": frappe.as_json(data),
        "status": "Completed"
    }).insert(ignore_permissions=True)
    return {"status": "ok"}
```

**Frappe as webhook sender:** Use the built-in Webhook DocType (Setup → Integrations → Webhook).

---

### Exposing Frappe with ngrok

ngrok creates a secure tunnel from a public URL to your local Frappe instance. Useful for testing webhooks, sharing dev sites, and OAuth callbacks.

**Setup:**

```bash
cd frappe-bench
bench pip install pyngrok

# Set your ngrok authtoken (from dashboard.ngrok.com)
bench --site mysite set-config ngrok_authtoken YOUR_TOKEN
bench --site mysite set-config http_port 8000

# Start bench first
bench start

# In another terminal, start ngrok tunnel
bench --site mysite ngrok --bind-tls
```

**Manual ngrok (alternative):**

```bash
ngrok authtoken YOUR_TOKEN  # One-time setup
ngrok http 8000
```

**Output:** `https://abc123.ngrok.io` — this URL forwards to your local `localhost:8000`.

**Alternatives:** Cloudflare Tunnel (`cloudflared`), localtunnel, pagekite.

**Important:** ngrok is for development/testing only. Never use it as a permanent production solution.

---

### Integration Request — Logging External API Calls

`Integration Request` is a Frappe DocType for tracking all outbound (and inbound) API calls. It provides a centralized audit trail for debugging integrations.

**Status lifecycle:** `Queued → Authorized → Completed / Failed / Cancelled`

**Basic usage:**

```python
from frappe.integrations.utils import create_request_log

def make_api_call(data):
    integration_request = create_request_log(
        data=data,
        service_name="MyAPI",
        request_headers={"Authorization": "Bearer token"},
        reference_doctype="Sales Invoice",
        reference_docname=data.get("invoice_id")
    )
    try:
        response = requests.post("https://api.example.com/endpoint", json=data)
        response.raise_for_status()
        integration_request.handle_success(response.json())
        return response.json()
    except Exception as e:
        integration_request.handle_failure({"error": str(e)})
        raise
```

**Query failed requests:**

```python
failed = frappe.get_all(
    "Integration Request",
    filters={"status": "Failed"},
    fields=["name", "integration_request_service", "error", "reference_doctype", "reference_docname"]
)
```

**Clean up old logs:**

```python
IntegrationRequest.clear_old_logs(days=30)
```

**Best practices:**
- Always include `reference_doctype` and `reference_docname` for traceability
- Use descriptive `service_name` values ("Stripe Payment", not "API")
- Handle all exception types (Timeout, ConnectionError, HTTPError)
- Cache results to avoid repeated API calls

---

### Building SPAs with Frappe and Doppio

**Doppio** is a Frappe app that scaffolds Single Page Applications (Vue/React) inside your custom Frappe app.

**Install:**

```bash
bench get-app https://github.com/NagariaHussain/doppio
bench new-app myapp
bench --site mysite install-app myapp
bench add-spa --app myapp --tailwindcss --typescript
```

**Project structure after scaffolding:**

```
myapp/
├── dashboard/              # SPA source (Vue/React)
│   ├── src/
│   ├── vite.config.js
│   └── proxyOptions.js
├── public/dashboard/       # Built assets (auto-created)
└── www/dashboard.html      # HTML entry point (auto-created)
```

**Configure proxy (`dashboard/proxyOptions.js`):**

```javascript
const frappeTargetPort = 8000;
const router = (req) => {
    const siteName = (req.headers.host || "").split(":")[0];
    return `http://${siteName}:${frappeTargetPort}`;
};

export default {
    "^/(app|api|assets|files|private)": {
        target: `http://127.0.0.1:${frappeTargetPort}`,
        ws: true,
        changeOrigin: true,
        router
    }
};
```

**Configure build (`dashboard/vite.config.js`):**

```javascript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import proxyOptions from "./proxyOptions";

export default defineConfig({
    plugins: [vue()],
    server: { port: 8080, proxy: proxyOptions },
    build: {
        outDir: "../myapp/public/dashboard",
        emptyOutDir: true,
    }
});
```

**Register routes in `hooks.py`:**

```python
website_route_rules = [
    {"from_route": "/dashboard/<path:app_path>", "to_route": "dashboard"},
    {"from_route": "/dashboard", "to_route": "dashboard"},
]
```

**Build for production:**

```bash
cd apps/myapp/dashboard
yarn build
```

**Development:**

```bash
yarn dev  # Runs on port 8080, proxies API to Frappe on 8000
```

**CDN alternative:** For adding Vue/React to specific Frappe forms without a full SPA setup, use CDN script tags directly in client scripts. No build process needed.

```html
<!-- In a custom HTML field or web page -->
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
<div id="app">{{ message }}</div>
<script>
Vue.createApp({ data() { return { message: "Hello from Vue!" } } }).mount("#app");
</script>
```
