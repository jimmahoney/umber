/*********************************************************
 * umber.js
 *
 * dependences :
 *   jquery.com
 *   underscorejs.org
 *   dropzonejs.com
 *
 * Jim Mahoney | cs.marlboro.edu | Sep 2017 | MIT License
 *********************************************************/

(function(){

    /*  function init_dropzone(){
     *   }
     */
    
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
     
	// Set handlers.
	$('.foldereditcheckbox').bind('click', handle_folder_edit_checkbox);
	$('#foldername').on('input propertychange paste', handle_create_folder);

	// Configure dopzone - see http://www.dropzonejs.com/#configuration.
        // (The form is in edit_folder.html and attachments.html).
	Dropzone.options.umberdropzone = {
	    maxFilesize: 5000,    	/* in MB ; default 256 ; 5000 ~ 5GB */

	    // see https://github.com/dropzone/dropzone/blob/main/src/options.js
	    // default options
	    //   uploadMultiple: false;  // in one request
	    //   chunking: false;        // if true, *all* files are chunked
	    //   parallelUploads: 2;
	};
    }

    $( init );
    
})();
