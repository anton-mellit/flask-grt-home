
function number_to_words(num, word) {
    if (num>=2) {
        return String(num) + " " + word + "s";
    }
    if (num==1) {
        return "1 "+word;
    }
    return "";
}

function time_in_words0_old(t) {
    t/=1000*60;
    var days = Math.floor(t/60/24);
    t -= days*60*24;
    var hours = Math.floor(t/60);
    t -= hours*60;
    var minutes = Math.floor(t);
    var res = [];
    if (days) {
        res.push(number_to_words(days, "day"));
    }
    if (hours) {
        res.push(number_to_words(hours, "hour"));
    }
    if (minutes) {
        res.push(number_to_words(minutes, "minute"));
    }
    if (res.length==3) {
        return res[0] + ", " + res[1] + ", and " + res[2];
    }
    if (res.length==2) {
        return res[0] + " and " + res[1];
    }
    if (res.length==1) {
        return res[0];
    }
    if (res.length==0) {
        return "a few seconds";
    }
}

function time_in_words0(t) {
    t/=1000*60;
    if (t>=1) {
        var days = Math.floor(t/60/24);
        if (days>=2) {
            days = Math.round(t/60/24);
            return number_to_words(days, "day");
        }
        t -= days*60*24;
        var hours = Math.floor(t/60);
        if (days>=1) {
            hours = Math.round(t/60);
            var res = "1 day";
            if (hours) {
                res += " and " + number_to_words(hours, "hour");
            }
            return res
        }
        t -= hours*60;
        var minutes = Math.round(t);
        var res = [];
        if (hours) {
            res.push(number_to_words(hours, "hour"));
        }
        if (minutes) {
            res.push(number_to_words(minutes, "minute"));
        }
        if (res.length==2) {
            return res[0] + " and " + res[1];
        }
        return res[0];
    }
    return "a few seconds";
}

function time_in_words(t) {
    if (t>=0) {
        return "in " + time_in_words0(t);
    } else {
        return time_in_words0(-t) + " ago";
    }
}

Dropzone.autoDiscover = false;

$(document).ready(function($) {
    $(".clickable").click(function() {
        window.document.location = $(this).data("href");
    });
    
    $(".date-time-long").each(function() {
        var time_str = this.dateTime;
        var d = new Date(time_str);
        var d_str = d.toLocaleString(undefined, { 
            weekday: 'short', month: 'short', 
            day: 'numeric', hour: '2-digit', 
            minute: '2-digit', hour12: false});
        var dif = d-new Date();
        if (dif<2*24*60*60*1000 && -dif<2*24*60*60*1000) {
            d_str += " (" + time_in_words(dif) + ")";
        }

        $(this).text(d_str);
    });

	$(".md-editor").each(function(){
		var simplemde = new SimpleMDE({
			element: this,
			forceSync: true,
			hideIcons: ["side-by-side", "fullscreen"],
			spellChecker: false,
			toolbar: ["bold", "italic", "heading", "|",
				"quote", "unordered-list", "ordered-list", "|",
				"link", "table", "|",
				"undo", "redo", "|",
				"preview", "guide"
			]
		});
	});    
    $( ".dropzone" ).each(function() {
        var paramsVal = { csrf_token: $(this).attr("csrf-token") };
        var param = $(this).attr("name");
        var options = {
            url: $(this).attr("upload-url"),
            params:paramsVal,
            addRemoveLinks: true,
            createImageThumbnails: false,
            thumbnail: function(file, dataUrl) {},
        };
        options = Object.assign(options, $(this).data("options"));

        var dz = new Dropzone( this, options );
        JSON.parse($( "#"+param ).val()).forEach(function(f) {
            var f2 = { name : f.name, type: f.type, size:f.size, accepted: true };
            dz.files.push(f2);
            dz.emit("addedfile", f2);
            dz.emit("complete", f2);
            // dz.displayExistingFile(f2, '', null, null, false);
        });

        $(this).parents("form").submit( function() {
            console.log("Submit");
            var form = this;
            var res = [];
            dz.getAcceptedFiles().forEach(function(f) {
                res.push({name: f.name, type: f.type, size: f.size});
            });
            console.log(JSON.stringify(res));
            $( "#"+param ).val(JSON.stringify(res));
        });
    });
});

