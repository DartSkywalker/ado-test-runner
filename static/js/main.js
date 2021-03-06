//--------------------------------------------------------------------------------------------
// Test Cases List

$('[data-toggle="popover"]').popover()

$('#statCase, .show_stat_mb3').on('click', function showCaseStatistics(e) {
    //Load data for statistics
    let runDate;
    let duration;
    let tester;
    let testResult;
    let adoId;
    let suiteName;
    let failureDetails;
    let failureStepNum;
    let failureStepComment;
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
                for (let i = 0; i < resp["duration"].length; i++) {
                    if (resp["duration"][i] !== "None") {
                        runDate = resp["date"][i];
                        duration = resp["duration"][i];
                        suiteName = resp["suite_name"][i];
                        tester = resp["tester"][i];
                        testResult = resp["state"][i];
                        failureDetails = resp["failure_details"][i];

                        if (testResult === 'Passed') {
                            testResult = "✅ &nbsp;Passed"
                            failureStepNum = failureDetails[0];
                            failureStepComment = failureDetails[1];

                            let dataStr = "";
                            for (let i=0;i < failureStepNum.length; i++) {
                                dataStr += '<p><b>Step #:</b>'+failureStepNum[i]+'<br\><b>Comment: </b>'+failureStepComment[i] + '</p>'
                            }

                            $('#statTable > tbody:last-child').append('<tr class="failure-row"><td>' + suiteName + '</td><td>' + tester + '</td><td>'
                                +
                                '<span data-trigger="hover" data-html="true" data-toggle="popover" title="Failed steps" data-content="'
                                +dataStr+'">' +
                                ''+testResult+'</span>\n'
                                +
                                '</td>' +
                                '<td>' + new Date(duration * 1000).toISOString().substr(11, 8) + '</td><td>' + runDate + '</td></tr>');
                                $('[data-toggle="popover"]').popover()
                        } else if (testResult === 'Failed') {
                            testResult = "❌ &nbsp;Failed"

                            failureStepNum = failureDetails[0];
                            failureStepComment = failureDetails[1];

                            let dataStr = "";
                            for (let i=0;i < failureStepNum.length; i++) {
                                dataStr += '<p><b>Step #:</b>'+failureStepNum[i]+'<br\><b>Comment: </b>'+failureStepComment[i] + '</p>'
                            }

                            $('#statTable > tbody:last-child').append('<tr class="failure-row"><td>' + suiteName + '</td><td>' + tester + '</td><td>'
                                +
                                '<span data-trigger="hover" data-html="true" data-toggle="popover" title="Failed steps" data-content="'
                                +dataStr+'">' +
                                ''+testResult+'</span>\n'
                                +
                                '</td>' +
                                '<td>' + new Date(duration * 1000).toISOString().substr(11, 8) + '</td><td>' + runDate + '</td></tr>');
                                $('[data-toggle="popover"]').popover()




                        } else if (testResult === 'Blocked') {
                            testResult = "🚫 &nbsp;Blocked"
                            failureStepNum = failureDetails[0];
                            failureStepComment = failureDetails[1];

                            let dataStr = "";
                            for (let i=0;i < failureStepNum.length; i++) {
                                dataStr += '<p><b>Step #:</b>'+failureStepNum[i]+'<br\><b>Comment: </b>'+failureStepComment[i] + '</p>'
                            }

                            $('#statTable > tbody:last-child').append('<tr class="failure-row"><td>' + suiteName + '</td><td>' + tester + '</td><td>'
                                +
                                '<span data-trigger="hover" data-html="true" data-toggle="popover" title="Failed steps" data-content="'
                                +dataStr+'">' +
                                ''+testResult+'</span>\n'
                                +
                                '</td>' +
                                '<td>' + new Date(duration * 1000).toISOString().substr(11, 8) + '</td><td>' + runDate + '</td></tr>');
                                $('[data-toggle="popover"]').popover()
                        } else if (testResult === 'Pause') {
                            testResult = "⏸ &nbsp;Pause"
                            failureStepNum = failureDetails[0];
                            failureStepComment = failureDetails[1];

                            let dataStr = "";
                            for (let i=0;i < failureStepNum.length; i++) {
                                dataStr += '<p><b>Step #:</b>'+failureStepNum[i]+'<br\><b>Comment: </b>'+failureStepComment[i] + '</p>'
                            }

                            $('#statTable > tbody:last-child').append('<tr class="failure-row"><td>' + suiteName + '</td><td>' + tester + '</td><td>'
                                +
                                '<span data-trigger="hover" data-html="true" data-toggle="popover" title="Failed steps" data-content="'
                                +dataStr+'">' +
                                ''+testResult+'</span>\n'
                                +
                                '</td>' +
                                '<td>' + new Date(duration * 1000).toISOString().substr(11, 8) + '</td><td>' + runDate + '</td></tr>');
                                $('[data-toggle="popover"]').popover()
                            }
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
    } else if (event.shiftKey) {
        document.getSelection().removeAllRanges();
        let targetRowIndex = $(this).parent().index();
        let activeRowIndex = $(document).find('tr.active').index();
        let tableRows = $('tr.clickable-row', '#mt')
        if (targetRowIndex > activeRowIndex) {
            for (let i = activeRowIndex; i <= targetRowIndex; i++) {
                $(tableRows[i]).addClass('active');
            }
        } else {
            for (let i = targetRowIndex; i <= activeRowIndex; i++) {
                $(tableRows[i]).addClass('active');
            }
        }
    } else if ($(this).closest('tr.clickable-row').hasClass('active')) {
        $(this).closest('tr.clickable-row').addClass('active').siblings().removeClass('active');
    } else {
        $(this).closest('tr.clickable-row').addClass('active').siblings().removeClass('active');
        $('#runCase').attr("href", window.location.href + "/" + $(this).closest('tr.clickable-row').children('td:first-child').children('a').attr('id'))
        $('.runTest').show();
        $('.statistics').show();
    }
});
$('body').on('dbclick', 'tr', function (event) {
    alert('asd')
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


//--------------------------------------------------------------------------------------------
