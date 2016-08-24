(function($){
  $(function(){

    $('.button-collapse').sideNav();
/*    $('.parallax').parallax();
    $('.scrollspy').scrollSpy();*/

    $('select').material_select();

    $(document).ready(function(){
	    // the "href" attribute of .modal-trigger must specify the modal ID that wants to be triggered
	    $('.modal-trigger').leanModal();
  	});

  }); // end of document ready
})(jQuery); // end of jQuery name space