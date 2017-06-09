$(function() {
  $('#result-form').submit(function() {
    console.log('submitted!');
    var license = $(this).find('select[name="license"]').val();
    console.log(license);

    $('#result-form').hide();


    if (license == '-') {
      $('#result-final-not-ok').show();
    } else {
      $('#result-final-ok').show();
    }

    return false;
  });
});
