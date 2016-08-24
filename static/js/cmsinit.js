(function($){
  $(function(){

    $('.button-collapse').sideNav();

    $('.datepicker').pickadate({
	    selectMonths: true, // Creates a dropdown to control month
	    selectYears: 15 // Creates a dropdown of 15 years to control year
  	});
  	$('select').material_select();

    // Medium Editor
    var elements = document.querySelectorAll('.editable'),
    editor = new MediumEditor(elements, {
    	paste: {
    		forcePlainText: true,
    		cleanPastedHTML: true,
    		cleanAttrs: ['class', 'style', 'dir']
    	},
    	buttons: ['bold', 'underline', 'anchor', 'removeFormat']
	});

	$("body").on("click", ".approve_blog", function(){
		var $this = $(this);
		var blog_id = $this.data("id");
		console.log(blog_id);
		if( $this.is(":checked") ){
			var approve_blog = true;
		}else{
			var approve_blog = false;
		};

		function success(data){
			if(data["message"] = "success"){
				console.log("approved blog");
			}else{
				alert("an error occurred");
			}
		};

		$.ajax({
			url: "/admin/approve_blog",
			type: 'post',
			data: {"blog_id": blog_id, "approve_blog": approve_blog},
			success: success
		}).fail(function(){
			alert("Ajax failed, an error occurred");
		});

	});

	//Dropzone file uploader
	//myAwesomeDropzone is the camelized version of the dropzone id, '#my-awesome-dropzone'
	/*Dropzone.options.myAwesomeDropzone = {
	  paramName: "image", // The name that will be used to transfer the file
	  maxFilesize: 20, // MB
	};*/

	/*Dropzone.options.myAwesomeDropzone = {
		maxFiles: 1,
	  	init: function() {
		    this.on("success", function(file, data) {
		    	console.log("file: ", file);
		    	console.log("data: ", data);
		    	if(data["message"] == "success"){
		    		$("#media_form_post_id").val(data["post_id"]);
		    		$("#text_form_post_id").val(data["post_id"]);
		    	};
		    });
	  	}
	};*/

  }); // end of document ready
})(jQuery); // end of jQuery name space