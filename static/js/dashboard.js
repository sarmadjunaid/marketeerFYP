document.addEventListener('DOMContentLoaded', function() {
    jQuery(function($){
            $('.male').each(function(i){
            $(this).click(function(){ $('#male_dd').eq(i).toggle();
            });
           });
       });
});

const spinnerBox = document.getElementById("spinner-box");
const dataBox = document.getElementById('gen_des');

$.ajax({
    type: 'GET',
    url: '/generate_description/',
    success: function(response){
        console.log(response);
    },
    error: function(error){
        console.log(error);
    }
})