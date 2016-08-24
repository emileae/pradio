/*$("body").on("change", "#url_id", function(){

  var url_id = $(this).val();

  console.log("blurring and looking for url")

  function success(data){
    if (data["message"] == "available"){
      $("#url_id").addClass("valid");
      $("#url_id").siblings("label").text("URL ID - "+data["message"]);
    }else{
      $("#url_id").addClass("invalid");
      $("#url_id").siblings("label").text("URL ID - "+data["message"]);
    };
  };

  $.ajax({
    url: "/admin/check_url",
    type: "post",
    data: {"url": url_id},
    success: success
  }).fail(function(){
    console.log("failed to check url id")
  });

})*/

$("body").on("submit", "form", function(){

  $(this).find(".loader-icon").removeClass("hide");

});



