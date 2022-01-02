forms_elems = document.getElementsByClassName("setup-form");

for(i=0; i<forms_elems.length; i++){
    forms_elems[i].addEventListener("submit", submitHandler);
}


function submitHandler(e){
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: e.target.action,
        data: $('#'+e.target.id).serialize(),
        dataType: 'json',
        complete: function (response) {
          var a = response;
          console.log(a);
          var b = response.responseText;
          console.log(b);
          var c = JSON.parse(response.responseText);
          console.log(c);

       }
    });
}
// ssl_session_cache shared:SSL:10m;
