

$("body").on("submit", ".generic_mailing_list_form", function(e){
  
  e.preventDefault();
  var name = $("#subscriber_name").val();
  var email = $("#subscriber_email").val();

  function success(data){
    $("#subscriber_name").val("");
    $("#subscriber_email").val("");
    $("#subscriber_email").removeClass("valid");

    $("#thank_you_subscribe").css("height", "4rem");
  };

  $.ajax({
    url: "/subscribe",
    type: "post",
    data: {
      "name": name, 
      "email": email,
    },
    success: success
  });

});

$("body").on("submit", "#email_share_form", function(e){
  
  e.preventDefault();
  var from_email = $("#from_email").val();
  var to_email = $("#to_email").val();
  var url = $("#email_share_url").val();

  function success(data){
    $("#from_email").val("");
    $("#to_email").val("");
    $("#from_email").removeClass("valid");
    $("#to_email").removeClass("valid");
    $("#thank_you_for_sharing").html(data["long_message"]);
    $("#thank_you_for_sharing").css("height", "4rem");
    if(data["long_message"] == "success"){
        setTimeout(function(){
          $('#email-modal').closeModal();
        }, 500)
    }else{
        setTimeout(function(){
          $('#email-modal').closeModal();
        }, 1500);
    };
  };

  $.ajax({
    url: "/send_share_email",
    type: "post",
    data: {
      "from_email": from_email, 
      "to_email": to_email,
      "url": url
    },
    success: success
  });

});

$("body").on("submit", "#unsubscribe_form", function(e){
  
  e.preventDefault();
  var email = $("#subscriber_email").val();

  console.log("ajax 1");

  function success(data){
    console.log("ajax 2");
    $("#subscriber_email").val("");
    $("#subscriber_email").removeClass("valid");

    $("#thank_you_unsubscribe").css("height", "4rem");
  };

  $.ajax({
    url: "/unsubscribe",
    type: "post",
    data: {
      "email": email,
    },
    success: success
  });

});

/* email share modal */
function openEmailModal(url){
  event.preventDefault();
  url = decodeURIComponent(url);
  url = url.split("?")[0];
  console.log("URL: ", url);
  $("#email_share_url").val(encodeURIComponent(url));
  $(".result-modal").closeModal();
  $('#email-modal').openModal();
};


$("body").on("submit", "#contact_form", function(e){
  
  e.preventDefault();
  var email = $("#email").val();
  var name = $("#name").val();
  var message = $("#message").val();
  var contact_type = $("#contact_type").val();

  function success(data){
    $("#email").val("");
    $("#name").val("");
    $("#message").val("");
    $("#email").removeClass("valid");
    $("#name").removeClass("valid");
    $("#message").removeClass("valid");
    $(".slide-out-notification").html(data["long_message"]);
    $(".slide-out-notification").css("height", "4rem");
  };

  $.ajax({
    url: "/contact",
    type: "post",
    data: {
      "email": email, 
      "name": name,
      "message": message,
      "contact_type": contact_type
    },
    success: success
  });

});







