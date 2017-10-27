/*********************************************************
 * umber.js
 *
 * dependences :
 *   jquery.com (3.2.1)
 *   underscorejs.org (1.8.3)
 *
 * The drag'n'drop code is adopted from 
 * https://github.com/kirsle/flask-multi-upload .
 *
 * Jim Mahoney | cs.marlboro.edu | Sep 2017 | MIT License
 *********************************************************/

(function(){

    function do_upload(files){

	// initialize progress bar
	var progressbar   = $("#progress-bar");
	var progresstext  = $("#progress-bar div");
	progressbar.show();
	progressbar.css({"width": "0%"});

	// put file information into a FormData object
	// and mark as ajax request (filedata will
	// be request.form in the backend python flask)
	var filedata = new FormData();
	_.each(files, function(f){filedata.append('file', f)});
	filedata.append('__ajax__', 'true');

	// debugging
	//for (var i=0; i<files.length; i++){
	//    alert(" files[" + i + "] : " + files[i].name + "," +
	//         files[i].size + "," + files[i].type);
	//    // i.e. :
	//    //    b.txt, 19, text/plain   <= file
	//    //    myfolder, 0,            <= folder
	//}
	
	// get upload url
	url_without_query = $(location).attr('href').replace(/\?.*/,'');
	upload_url =  url_without_query + '?action=upload';
	// alert("upload url = '" + upload_url + "'");
	    
	// set up and invoke an async ajax upload via jquery
	// (xhr is "xml http request")
	var xhr = $.ajax({
	    url: upload_url,
	    data: filedata,
	    method: 'POST',
	    contentType: false,
	    processData: false,
	    cache: false,
	    sucess: function(data){
		progressbar.css({"width": "100%"});
		data = JSON.parse(data);
		if (data.status === "error"){
		    // TODO - better error reporting
		    alert("OOPS : upload error '" + data.msg + "'")
		}
		else {
		    // SUCCESS ... anything else needed here?
		    progressbar.hide();
		}
	    },
	    xhr: function(){
		// upload in progress
		var xhrobj = $.ajaxSettings.xhr();
		if (xhrobj.upload){
		    xhrobj.upload.addEventListener("progress",
			    function(event) {
			        var percent = 0;
			        var position = event.loaded || event.position;
			        var total    = event.total;
			        if (event.lengthComputable) {
				    percent = Math.ceil(position / total * 100);
			        }
			        // Set the progress bar.
			        progressbar.css({"width": percent + "%"});
			        progresstext.text(percent + "%");
			    }, false)
		}
		return xhrobj;
	    }         // xhr: function
	});           // $.ajax
    }                 // function do_upload
    
    function init_dragndrop(){
	
	var dragndrop = $("#dragndrop");
	if (dragndrop){

	    dragndrop.on("dragover", function(e){
		e.stopPropagation();
		e.preventDefault();
	    });

	    dragndrop.on("dragenter", function(e){
		e.stopPropagation();
		e.preventDefault();
		$(this).css('border', '3px dashed #606000');
		$(this).css('background',
		    'url(/static/images/file_add.png) no-repeat center');
	    });

	    dragndrop.on("dragexit", function(e){
		e.stopPropagation();
		e.preventDefault();
		$(this).css('border', '3px solid transparent');
		$(this).css('background', 'none');
	    });
	    
	    dragndrop.on("drop", function(e){
		e.preventDefault();
		$(this).css('border', '3px solid transparent')
		$(this).css('background', 'none');

		//var dt = e.originalEvent.dataTransfer;
		//alert(" Data Transfer Items: " + dt.items );
		// See  
		// developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry
		// If I were handling folder uploads here,
		// this is where each dt.items would be checked to see
		// if it was a folder, and if so, handled recursively.
		
		// dataTransfer.files can contain folders, which I don't want.
		// To check, I'm only keeping those with nonzero size.
		var files = _.filter(e.originalEvent.dataTransfer.files,
				     function(f){return f.size > 0});
		if (files.length > 0){
		    do_upload(files);
		}
		
	    });	    
	}

	// If a file is dropped outside of the drop zone,
	// browsers will by default redirect to display that file.
	// To avoid that behavior, this method disables the
	// 'drop' event on the document.
	function stopDefault(e) {
	    //alert(" stop default" );
            e.stopPropagation();
            e.preventDefault();
	}
	$(document).on("dragenter", stopDefault);
	$(document).on("dragover", stopDefault);
	$(document).on("drop", stopDefault);
    }
    
    function any_folder_checkbox(){
	/*  true if any checkbox in the folder edit form is checked. */
	return _.some( $('.foldereditcheckbox'),
		       function(b){return b.checked } );
    }
    
    function handle_folder_edit_checkbox(){
	/* One of the check boxes in the folder edit page has been clicked. */
	if (any_folder_checkbox()){
	    $('#folderdeletebutton').prop('disabled', false)
                      	            .addClass('enabledbutton')
	                            .removeClass('disabledbutton');
	}
	else {
	    $('#folderdeletebutton').prop('disabled', true)
                      	            .removeClass('enabledbutton')
	                            .addClass('disabledbutton');
	}
    }

    function handle_create_folder(){
	/* Text has been entered in 'New folder' */
	if ($('#foldername').val().length > 0){
	    $('#foldercreatebutton').prop('disabled', false)
                      	            .addClass('enabledbutton')
	                            .removeClass('disabledbutton');
	}
	else {
	    $('#foldercreatebutton').prop('disabled', true)
                      	            .removeClass('enabledbutton')
	                            .addClass('disabledbutton');
	}
    }

    
    function init(){
     
	// Set handlers for buttons & drag'n'drop in the folder edit folder page.
	$('.foldereditcheckbox').bind('click', handle_folder_edit_checkbox);
	$('#foldername').on('input propertychange paste', handle_create_folder);
	init_dragndrop();
	
    }

    $( init );
    
})();

