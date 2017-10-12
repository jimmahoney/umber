/*********************************************************
 * umber.js
 *
 * dependences :
 *   jquery.com (3.2.1)
 *   underscorejs.org (1.8.3)
 *
 * Jim Mahoney | cs.marlboro.edu | Sep 2017 | MIT License
 *********************************************************/

(function(){

    function any_folder_checkbox(){
	/*  true if any checkbox in the folder edit form is checked. */
	return _.some( $('.foldereditcheckbox'),
		       function(b){return b.checked } );
    }
    
    function handle_folder_edit_checkbox(){
	/* One of the check boxes in the folder edit page has been clicked. */
	if (any_folder_checkbox()){
	    $('#folderdeletebutton').prop('disabled', false)
                      	            .addClass('enabledelete')
	                            .removeClass('disableddelete');
	}
	else {
	    $('#folderdeletebutton').prop('disabled', true)
                      	            .removeClass('enabledelete')
	                            .addClass('disableddelete');
	}
    }
    
    function init(){
	$('.foldereditcheckbox').bind('click', handle_folder_edit_checkbox);
    }

    $( init );
    
})();

