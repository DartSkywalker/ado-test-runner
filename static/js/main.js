
//--------------------------------------------------------------------------------------------
// Test Cases List
$('#statCase').on('click', function (e) {
    //Load data for statistics
    let runDate;
    let duration;
    let tester;
    let testResult;
    let adoId;
    let suiteName;
    let testSuiteId = window.location.href.substr(window.location.href.lastIndexOf("/")).replace("/", "");

    $("#mt tr.active").each(function () {
        if (true) {
            // tester = $(this).find('td:nth-child(4)').text().trim();
            // testResult = $(this).find('td:nth-child(3)').text().trim();
            adoId = $(this).find('td:nth-child(1)').text().trim();

            $.ajax({
                url: "/getstatistics/" + testSuiteId + "/" + adoId,
                type: 'GET'
            }).done(function (responseData) {
                console.log('Done: ', responseData);
                let resp = JSON.parse(responseData)
                $("#statTable > tbody").empty();
                for (let i = 0; i < resp["duration"].length; i++){
                    if (resp["duration"][i] !== "None") {
                       runDate = resp["date"][i];
                       duration = resp["duration"][i];
                       suiteName = resp["suite_name"][i];
                       tester = resp["tester"][i];
                       testResult = resp["state"][i];

                       if (testResult === 'Passed') {
                           testResult = "✅ &nbsp;Passed"
                       } else if (testResult === 'Failed') {
                           testResult = "❌ &nbsp;Failed"
                       } else if (testResult === 'Blocked') {
                           testResult = "🚫 &nbsp;Blocked"
                       }

                       $('#statTable > tbody:last-child').append('<tr><td>' + suiteName + '</td><td>' + tester + '</td><td>' + testResult + '</td>' +
                        '<td>' + new Date(duration * 1000).toISOString().substr(11, 8) + '</td><td>' + runDate + '</td></tr>');
                    }
                }
            }).fail(function () {
                console.log('Failed');
                alert("Cannot load statistics. Internal Server Error");
            });

            $('.statPopUp').css("display", "block")
        }
    });
});

// If the target of the click isn't the container
$(document).mouseup(function (e) {
    var container = $(".statPopUp");
    if (!container.is(e.target) && container.has(e.target).length === 0) {
        $('.statPopUp').css("display", "none")
    }
});

$(document).ready(function () {
        $(".set-user").on('change', function () {
            let userId;
            if ($("#mt tr.active").length > 1) {
                $("#mt tr.active:first").each(function () {
                    userId = $(this).find("select.set-user:first-child").val();
                    console.log(userId)
                });
                $("#mt tr.active").each(function () {
                    $(this).find("select.set-user:first-child").val(userId);
                    toSave = {};
                    toSave['userid'] = userId;
                    var testCaseId = $(this).closest('tr').find('td.tcid').text().trim();
                    let suiteId = window.location.href.substr(window.location.href.lastIndexOf("/")).replace("/", "");
                    $.ajax({
                        url: "/save_user/" + suiteId + "/" + testCaseId,
                        data: JSON.stringify(toSave),
                        type: 'POST',
                        contentType: 'application/json'
                    }).done(function (responseData) {
                        console.log('Done: ', responseData);
                    }).fail(function () {
                        console.log('Failed');
                    });
                });
            } else {

                toSave = {};
                userId = $(this).val();
                toSave['userid'] = userId;

                var testCaseId = $(this).closest('tr').find('td.tcid').text().trim();

                let suiteId = window.location.href.substr(window.location.href.lastIndexOf("/")).replace("/", "");
                $.ajax({
                    url: "/save_user/" + suiteId + "/" + testCaseId,
                    data: JSON.stringify(toSave),
                    type: 'POST',
                    contentType: 'application/json'
                }).done(function (responseData) {
                    console.log('Done: ', responseData);
                }).fail(function () {
                    console.log('Failed');
                });
            }
        });
});

$('#mt tr.clickable-row td:nth-child(2)').on('click', function (event) {
        if (event.altKey) {

            $(this).closest('tr.clickable-row').addClass('active');
            $('.runTest').hide();
            $('.statistics').hide();
        } else if ($(this).closest('tr.clickable-row').hasClass('active')) {

        } else {
            $(this).closest('tr.clickable-row').addClass('active').siblings().removeClass('active');
            $('#runCase').attr("href", window.location.href + "/" + $(this).closest('tr.clickable-row').children('td:first-child').text().trim())
            $('.runTest').show();
            $('.statistics').show();

        }
});

//--------------------------------------------------------------------------------------------
//Signup
$('.help-icon-reg').popover();

$(document).on('click', '#signup', function (e) {
    e.preventDefault();
    let username = $("#username").val();
    let token = $("#token").val();
    let inviteCode = $("#invite").val();
    let password = $("#password").val();

        $.ajax({
            type: "POST",
            url: "/signup",
            data: JSON.stringify({
                username: username,
                token: token,
                invite: inviteCode,
                password: password,
            }),
            contentType: 'application/json',
            success: function (result) {
                $(location).attr('href', '/login')
            },
            error: function (result) {
                alert('Invalid Invite Code. Please, double check it and try again.')
            }
        });

})

//New Registration
    const sign_in_btn = document.querySelector("#sign-in-btn");
    const sign_up_btn = document.querySelector("#sign-up-btn");
    const container = document.querySelector(".container");

    sign_up_btn.addEventListener("click", () => {
        container.classList.add("sign-up-mode");
    });

    sign_in_btn.addEventListener("click", () => {
        container.classList.remove("sign-up-mode");
    });

//--------------------------------------------------------------------------------------------
//Settings

$("#save").on("click", function (e) {
        e.preventDefault();
        let token = $("#token").val();
        $.ajax({
            type: "POST",
            url: "/settings",
            data: JSON.stringify({token: token}),
            contentType: 'application/json',
            success: function (result) {
                $("#saveSuccess").css('display', 'flex')
                $("#saveSuccess").fadeOut(3000)
            },
            error: function (result) {
                $("#saveFailed").css('display', 'flex')
                $('#token').addClass('errorHighlight');
                setTimeout(function () {
                    $('#token').removeClass('errorHighlight');
                }, 3000);
                $("#saveFailed").fadeOut(3000)
            }
        });
    });

$(document).on('click','#savePassword',function(e) {
    e.preventDefault();
    let newPass = $("#newPass").val();
    let newPassConfirm = $("#newPassConfirm").val();

    if (newPass === newPassConfirm) {
        $.ajax({
            type: "POST",
            url: "/changepass",
            data: JSON.stringify({newpass: newPass}),
            contentType: 'application/json',
            success: function (result) {
                $("#saveSuccess").css('display', 'flex')
                $("#saveSuccess").fadeOut(3000)
            },
            error: function (result) {
                $("#saveFailed").css('display', 'flex')
                $('#newPass').addClass('errorHighlight');
                $('#newPassConfirm').addClass('errorHighlight');
                setTimeout(function () {
                    $('#newPassConfirm').removeClass('errorHighlight');
                    $('#newPass').removeClass('errorHighlight');
                }, 3000);
                $("#saveFailed").fadeOut(3000)
            }
        });
    }
})

//--------------------------------------------------------------------------------------------
