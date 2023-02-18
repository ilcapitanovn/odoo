function left(str, n) {
    if (n <= 0)
        return "";
    else if (n > String(str).length)
        return str;
    else
        return String(str).substring(0, n);
}

function right(str, n) {
    if (n <= 0)
        return "";
    else if (n > String(str).length)
        return str;
    else {
        var iLen = String(str).length;
        return String(str).substring(iLen, iLen - n);
    }
}

function isNumberKey(evt)
{
	 var charCode = (evt.which) ? evt.which : event.keyCode
	 if (charCode > 31 && (charCode < 48 || charCode > 57))
	 return false;
	 return true;
}

function printtk(url,data){
	window.open("/"+url+"?"+data);
}

function countDownTimer(className, startDate, endDate, regexpReplaceWith) {
	$("#" + className).countdowntimer({
		startDate: startDate,
		dateAndTime: endDate,
		size: "lg",
		regexpMatchFormat: "([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})",
		regexpReplaceWith: regexpReplaceWith
	});
}

function formatDate(date) {

  var day = date.getDate();
  var month = date.getMonth()+1;
  var year = date.getFullYear();
  var h = date.getHours();
  var i = date.getMinutes();
  var s = date.getSeconds();
  
  return month + '/' + day + '/' + year + ' ' + h + ':' + i + ':' + s;
}

function getnew_code() {
    var manhung;
    manhung = '<div id="mc_embed" data-id="' + $("#box_kqxs_tinhx").val() + '" size="' + $("#slsize").val() + '"></div>\n<script src="//' + document.domain + '/embed/minhchinh.js"></script>';

    $("#manhung").val(manhung);

    $("#xemtruoc").html('<div id="mc_embed" data-id="' + $("#box_kqxs_tinhx").val() + '" size="' + $("#slsize").val() + '"></div><script src="//' + document.domain + '/embed/minhchinh.js"></script>');

}

function setActive(e) {
    $(e + " li a").each(function(index, element) {
        if (document.location.href.indexOf($(this).attr("href")) >= 0 && $(this).attr("href") != '/') {
            //$(this).parent("li").children("ul").show();
            //$(this).parent("li").parent("ul").show();
            $(this).addClass("active");
            $(this).parent("li").parent("ul").parent("li").children("a").addClass("active");
        }
    });
}

function setActiveTab(e) {
    $(e + " li a").click(function(even){
		even.preventDefault();
		if( !$(this).parent().hasClass('current') ){
			$(e + " li").removeClass('current');
			$(this).parent().addClass('current');
			tab=$(this).attr('href');
			$(".content_tab").hide();
			$(tab).show();
		}
	});
}

function setActiveMenu(e) {
    $(e).click(function(even){
		$(this).parent('li').toggleClass('current');
		$(this).parent('li').find('.content-daily').slideToggle(500);
	});
}
setActiveMenu('.nav-daily .more-daily');

function getajaxcontent(e, t, n) {
    $("#" + e).html('<center><img src="/images/processing.gif"><br>Đang xử lý...<center>');
    $.ajax({
        type: "GET",
        url: t,
        data: n,
        success: function(t) {
            $("#" + e).html(t)
        }
    })
}

function clearDot(e) {
    var t = "",
        n = 0,
        r = "";
    if (e != "") {
        var s = e.length;
        r = e.substr(0, 1);
        if (r == "-") {
            n = 1;
            t = "-"
        }
        for (i = n; i < s; i++) {
            if (e.substr(i, 1) != "." && e.substr(i, 1) != "-" && !isNaN(e.substr(i, 1))) t = t + e.substr(i, 1)
        }
    }
    return t
}

function convert(e) {
    var t = $(e).val(),
        n = "",
        r = 0,
        s = "";
    var o = clearDot(t);
    if (o != "") {
        var u = o.length - 1;
        s = o.substr(0, 1);
        if (s == "-") {
            r = 1
        } else s = "";
        k = 0;
        for (i = u; i >= r; i--) {
            k++;
            n = o.substr(i, 1) + n;
            if (o.substr(i, 1) == ".") {
                k = 0
            }
            if (k == 3 && i > r) {
                k = 0;
                n = n
            }
        }
    }
    e.value = s + n
}
function getBrowser()
{
var nVer = navigator.appVersion;
var nAgt = navigator.userAgent;
var browserName  = navigator.appName;
var fullVersion  = ''+parseFloat(navigator.appVersion); 
var majorVersion = parseInt(navigator.appVersion,10);
var nameOffset,verOffset,ix;

// In Opera 15+, the true version is after "OPR/" 
if ((verOffset=nAgt.indexOf("OPR/"))!=-1) {
 browserName = "Opera";
 fullVersion = nAgt.substring(verOffset+4);
}
// In older Opera, the true version is after "Opera" or after "Version"
else if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
 browserName = "Opera";
 fullVersion = nAgt.substring(verOffset+6);
 if ((verOffset=nAgt.indexOf("Version"))!=-1) 
   fullVersion = nAgt.substring(verOffset+8);
}
// In MSIE, the true version is after "MSIE" in userAgent
else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
 browserName = "Netscape";
 fullVersion = nAgt.substring(verOffset+5);
}
// In Chrome, the true version is after "Chrome" 
else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
 browserName = "Chrome";
 fullVersion = nAgt.substring(verOffset+7);
}
// In Safari, the true version is after "Safari" or after "Version" 
else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
 browserName = "Safari";
 fullVersion = nAgt.substring(verOffset+7);
 if ((verOffset=nAgt.indexOf("Version"))!=-1) 
   fullVersion = nAgt.substring(verOffset+8);
}
// In Firefox, the true version is after "Firefox" 
else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
 browserName = "Firefox";
 fullVersion = nAgt.substring(verOffset+8);
}
// In most other browsers, "name/version" is at the end of userAgent 
else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < 
          (verOffset=nAgt.lastIndexOf('/')) ) 
{
 browserName = nAgt.substring(nameOffset,verOffset);
 fullVersion = nAgt.substring(verOffset+1);
 if (browserName.toLowerCase()==browserName.toUpperCase()) {
  browserName = navigator.appName;
 }
}
// trim the fullVersion string at semicolon/space if present
if ((ix=fullVersion.indexOf(";"))!=-1)
   fullVersion=fullVersion.substring(0,ix);
if ((ix=fullVersion.indexOf(" "))!=-1)
   fullVersion=fullVersion.substring(0,ix);

majorVersion = parseInt(''+fullVersion,10);
if (isNaN(majorVersion)) {
 fullVersion  = ''+parseFloat(navigator.appVersion); 
 majorVersion = parseInt(navigator.appVersion,10);
}

return browserName;
}
function getajaxcontentnoprocessing(e, t, n) {
    $.ajax({
        type: "GET",
        url: t,
        data: n,
        success: function(t) {
            $("#" + e).html(t)
        }
    })
}

function onof(e, t) {
    document.getElementById(e).style.display = "";
    document.getElementById(t).style.display = "none"
}

function closeid(e) {
    $("#" + e).hide()
}

function openurl(e) {
    window.location = e
}

function getajaxcontenton(e, t, n) {
    $("#" + e).append('<div class="onidprocess"><img src="/images/processing.gif"></div>');
    $.ajax({
        type: "GET",
        url: t,
        data: n,
        success: function(t) {
            $("#" + e).html(t)
        }
    })
}

function setCookie(e, t, n) {
    var r = new Date;
    r.setDate(r.getDate() + n);
    var i = escape(t) + (n == null ? "" : "; expires=" + r.toUTCString());
    document.cookie = e + "=" + i + "; path=/"
}

function getCookie(c_name) {
    var i, x, y, ARRcookies = document.cookie.split(";");
    for (i = 0; i < ARRcookies.length; i++) {
        x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
        y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
        x = x.replace(/^\s+|\s+$/g, "");
        if (x == c_name) {
            return unescape(y);
        }
    }
    return "";
}


function SetUserLocation(position) {
    $.ajax({
        type: "GET",
        url: "/ajax/setUserLocation.php",
        data: "lat=" + position.coords.latitude + "&lng=" + position.coords.longitude,
        success: function(t) {
            setCookie("usgl", "1", 30);

        }
    })
}

function changecssclass() {
    if (window.innerHeight > window.innerWidth) {
		if (window.innerHeight / window.innerWidth < 1.4) {
			$("#bangtructiep").attr("class", "bangtructiepH");
			var tylewh = window.innerWidth / window.innerHeight;
			$("#bangtructiep").width(1024 * tylewh);
		} else {
			$("#bangtructiep").attr("class", "bangtructiepH");
			var tylewh = window.innerWidth / window.innerHeight;
			$("#bangtructiep").width(1280 * tylewh);
		}
	} else {
		if (window.innerWidth / window.innerHeight < 1.5) {
			$("#bangtructiep").attr("class", "bangtructiepW43");
			var tylewh = window.innerWidth / window.innerHeight;
			$("#bangtructiep").width(768 * tylewh);
		} else {
			$("#bangtructiep").attr("class", "bangtructiepW");
			var tylewh = window.innerWidth / window.innerHeight;
			$("#bangtructiep").width(720 * tylewh);
		}
	}

	var zw = window.innerWidth / $("#bangtructiep").width();
	var zh = window.innerHeight / $("#bangtructiep").height();
	var zoom;
	if (zw > zh) zoom = zh;
	else
		zoom = zw;
	$("#bangtructiep").css("top", (window.innerHeight - $("#bangtructiep").height()) / 2 + "px");
	$("#bangtructiep").css("left", (window.innerWidth - $("#bangtructiep").width()) / 2 + "px");

	setTimeout(function() {
		$("#bangtructiep").css("-moz-transform", "scale(" + zoom + ")");
		$("#bangtructiep").css("-webkit-transform", "scale(" + zoom + ")");
		$("#bangtructiep").css("-o-transform", "scale(" + zoom + ")");
	}, 500);
}

function setToolBkqxs() {
    var siteDomain = "http://" + document.domain;
    $(".btnlinkprint").click(function(e) {
        var idp = $(this).attr("data-id");
		idp=idp.split('|');
        var loaixs=idp[0];
	    var ngay=idp[1];
		print_vedo(loaixs, ngay);
    });
	
	$(".btnthongke").click(function(e) {
        var idp = $(this).attr("data-id");
		idp=idp.split('|');
        var loaixs=idp[0];
	    var ngay=idp[1];
		window.location = "/thong-ke-xo-so-"+loaixs+".html";
		//print_thongke(loaixs, ngay);
    });
	
    $(".btnlinkprinttt").click(function(e) {
        var idp = $(this).attr("data-id");
		idp=idp.split('|');
        print_vedo_tructiep(idp[0],idp[1]);
    });
	

    $(".btnshare").click(function(e) {
		var a = 'https://www.facebook.com/sharer/sharer.php?u=' + siteDomain;
		window.open(a, "share", "height=400,width=600");
		return false
	});

    $(".btnsharett").click(function(e) {
        if ($(this).hasClass('clicked')) {
            $(this).removeClass('clicked');
            $(".boxsharekqxs").remove();

        } else {
            $(this).addClass('clicked');
            var id = left($(this).attr("data-id"), 1);
            var date = right($(this).attr("data-id"), 10);
            var title = ["Kết Quả Xổ Số", "Trực Tiếp Xổ Số Miền Nam", "Trực Tiếp Xổ Số Miền Bắc", "Trực Tiếp Xổ Số Miền Trung"];
            var url = ["/ket-qua-xo-so/", "/truc-tiep-xo-so-mien-nam.html", "/truc-tiep-xo-so-mien-bac.html", "/truc-tiep-xo-so-mien-trung.html"];

            var ids = $(this).attr("data-id");
            $(".bangkqxs_link").after('<div class="boxsharekqxs"><div class="embed-share group">  <label style="float:left">Chia sẻ:</label>  <a href="#" name="zm_share" class="buttonimage icon32 fn-share-zing" title="Chia sẻ lên Zing Me" target="_blank">Zing Me</a><a href="#" class="buttonimage icon32 fn-share-fb" title="Chia sẻ lên Facebook">Facebook</a><a href="#" class="buttonimage icon32 fn-share-gplus" title="Chia sẻ lên Google+">Google plus</a><input type="button" class="btnsavekqxs" value="Lưu Hình KQXS"/> </div><form id="frm' + ids + '" action="/download.php" method="post"><input id="id" name="id" type="hidden" value=""><input id="image" name="image" type="hidden" value=""></form></div>');

            $(".btnsavekqxs").click(function(e) {
                html2canvas($(".box_kqxs"), {
                    onrendered: function(canvas) {
                        var dataURL = canvas.toDataURL();
                        $("#frm" + ids + " #image").val(dataURL);
                        $("#frm" + ids + " #id").val(ids);
                        $("#frm" + ids).submit();

                    }
                });
            });
            $(".fn-share-zing").click(function() {
                var a = "http://link.apps.zing.vn/share?u=" + siteDomain + url[id]  + "&t=" + title[id] + ' ngày ' + date + " - Xổ Số Minh Chính";
                window.open(a, "share", "height=400,width=600");
                return false
            });
            $(".fn-share-fb").click(function() {
                var a = 'https://www.facebook.com/sharer/sharer.php?u=' + siteDomain + url[id];
                window.open(a, "share", "height=400,width=600");
                return false
            });
            $(".fn-share-gplus").click(function() {
                var a = "https://plus.google.com/share?url=" + siteDomain + url[id]+"&t=" + title[id] + ' ngày ' + date + ' - Xổ Số Minh Chính';
                window.open(a, "share", "height=400,width=600");
                return false
            })



        }
    });
    $(function() {
        // check native support

        // open in fullscreen
        $('.btnfullsize').click(function() {
            var idf = $(this).attr('data-id');
			idf = idf.split('|');
			var idbox='fullscreen';
			var title='Mega 6/45';
			var css='';
            //$("#box_tructiepkqxs").remove();
			if(idf[0]=='max-4d'){
				 idbox='fullscreenMax4D';
				 title='Max 4D';
			}
			else if(idf[0]=='power-655'){
				 idbox='fullscreen';
				 css='fullscreenPower655';
				 title='Power 6/55';
			}
			else if(['max-3d','max3d-pro'].includes(idf[0])){
				 idbox='fullscreenMax4D';
				 css='fullscreenMax3D';
				 title='Max 3D';
			}
            $('body').prepend('<div id="'+idbox+'" class="'+css+'"><div class="headertructiep"><div class="headerlogo"><div class="logo"><img alt="" border="0" hspace="0" src="/upload/images/logo_ketquadientoan.png" vspace="0"></div><div class="title_header">Xổ số tự chọn '+title+'</div></div></div><button class="miximize_icon"></button><div id="bangtructiep" class="bangtructiepH"></div></div>');
            $("body").css({
                overflow: 'hidden'
            });
            $('#'+idbox).fullscreen();

            $.ajax({
                type: "GET",
                url: '/ajax/fullview.php',
                data: 'loaixs=' + idf[0] + '&ngay=' + idf[1],
                success: function(t) {
                    $("#bangtructiep").html(t);
                    changecssclass();
                }
            });

            // exit fullscreen
            $('.miximize_icon').click(function() {

                $.fullscreen.exit();
                $("#"+idbox).remove();
                window.location = window.location + "";
                return false;

            });

            return false;
        });
		
		
		$('#btnfullsizehome li').click(function() {
            var loaixs = $(this).attr('val');
			var id='fullscreenhome';
			var css='fullscreenhomeH';
			if(loaixs=='power-655'){
				id='fullscreen';
				css='fullscreenPower655';
			}else if(loaixs=='mega-6-45'){
				id='fullscreen';
				css='';
			}else if(loaixs=='max-4d'){
				id='fullscreenMax4D';
				css='';
			}else if(['max-3d', 'max3d-pro'].includes(loaixs)){
				 id='fullscreenMax4D';
				 css='fullscreenMax3D';
			}
            $('body').prepend('<div id="'+id+'" class="'+css+'"><button class="miximize_icon"></button><div id="bangtructiep" class="bangtructiepH"></div></div>');
            $("body").css({
                overflow: 'hidden'
            });
            $('#'+id).fullscreen();

            $.ajax({
                type: "GET",
				cache: false,
                url: '/ajax/fullview.php',
                data: 'loaixs='+loaixs,
                success: function(t) {
                    $("#bangtructiep").html(t);
                    changecssclass();
                }
            });

            // exit fullscreen
            $('.miximize_icon').click(function() {

                $.fullscreen.exit();
                $("#"+id).remove();
                window.location = window.location + "";
                return false;

            });

            return false;
        });
    });
}
$(this).resize(function(e) {
    changecssclass();
});

function printxs(e) {
	$("#frminkq").attr('action','/ve-do.php');
    $("#page").val(e);
	$("#pagenew").val(e);
    if ($("#txttitle").attr("title") != $("#txttitle").val()) {
        $("#txttitle").attr("name", "txttitle")
    }
	else $("#frminkq").submit();
	
    $(".dailog_bog").dialog("close");
    return false
}

function removeStyle(){
	$(".btn-nav").removeClass("active");
	$(".topnav, .navbar, .navbar ul").removeAttr("style");
	$(".bg-overlay").fadeOut("fast");
}

function print_vedo(e, t) {
			
    $(".dailog_bog").dialog({
        modal: true,
        open: function() {
            $(this).html('<form action="/ve-do.php" method="get" name="frminkq" target="vedo" id="frminkq"><table border="0" align="center" cellpadding="0" cellspacing="0"><tr><td align="center"><img src="/upload/images/in-ve-do-4-bang.png" width="79" height="98"  onclick="printxs(4);" /></td><td width="20" align="center">&nbsp;</td><td width="20" align="center">&nbsp;</td><td align="center"><img src="/upload/images/in-ve-do-6-bang.png" width="79" height="98"  onclick="printxs(6);" /></td><td width="20" align="center">&nbsp;</td><td width="20" align="center">&nbsp;</td><td align="center"><img src="/upload/images/in-ve-do-1-bang.png" width="79" height="98"  onclick="printxs(1);"/></td></tr><tr><td align="center"><input name="loaixs" type="hidden" value="' + e + '" /><input name="page" id="page" type="hidden" value="0" /><input class="btninvedo" onClick="printxs(4);" type="button" value="In 4/1" /></td><td align="center">&nbsp;</td><td align="center">&nbsp;</td><td align="center"><input class="btninvedo" onClick="printxs(6);" type="button" value="In 6/1" /></td><td align="center">&nbsp;</td><td align="center">&nbsp;</td><td align="center"><input class="btninvedo" onClick="printxs(1);" type="button" value="In 1/1" /></td></tr></table><input name="ngay" type="hidden" value="' + t + '"></form>');
        }, 
		width: 350,
        title: "Chọn loại vé dò cần in"
    });
}

function print_vedo_tructiep(e, t) {
    $(".dailog_bog").dialog({
        modal: true,
        open: function() {
            $(this).html('<form action="/ve-do.php" method="get" name="frminkq" target="vedo" id="frminkq"><table border="0" align="center" cellpadding="0" cellspacing="0"><tr><td align="center"><img src="/upload/images/in-ve-do-4-bang.png" width="79" height="98"  onclick="printxs(4);" /></td><td width="20" align="center">&nbsp;</td><td width="20" align="center">&nbsp;</td><td align="center"><img src="/upload/images/in-ve-do-6-bang.png" width="79" height="98"  onclick="printxs(6);" /></td><td width="20" align="center">&nbsp;</td><td width="20" align="center">&nbsp;</td><td align="center"><img src="/upload/images/in-ve-do-1-bang.png" width="79" height="98"  onclick="printxs(1);"/></td></tr><tr><td align="center"><input name="loaixs" type="hidden" value="' + e + '" /><input name="page" id="page" type="hidden" value="0" /><input class="btninvedo" onClick="printxs(4);" type="button" value="In 4/1" /></td><td align="center">&nbsp;</td><td align="center">&nbsp;</td><td align="center"><input class="btninvedo" onClick="printxs(6);" type="button" value="In 6/1" /></td><td align="center">&nbsp;</td><td align="center">&nbsp;</td><td align="center"><input class="btninvedo" onClick="printxs(1);" type="button" value="In 1/1" /></td></tr></table><input name="ref" type="hidden" value="xstt"><input name="ngay" type="hidden" value="' + t + '"></form>');
        },
        width: 350,
        title: "Chọn loại vé dò cần in"
    });
}

function print_thongke(e, t) {
    $(".dailog_bog").dialog({
        modal: true,
        open: function() {
            $(this).html('<form method="get" name="frminkq" target="vedo" id="frminkq"><table border="0" align="center" cellpadding="0" cellspacing="0"><tr><td align="center"><a href="/thong-ke-xo-so-'+e+'.html?type=thongke" title="Thống kê kết quả điện toán"><img src="/upload/images/thong_ke.jpg" height="90" /></a></td><td width="20" align="center">&nbsp;</td><td width="20" align="center">&nbsp;</td><td align="center"><a href="/thong-ke-xo-so-'+e+'.html?type=bieudo" title="Biểu đồ kết quả điện toán mega 6/45"><img src="/upload/images/bieu_do.jpg" height="90" /></a></td></tr><tr><td align="center"><a href="/thong-ke-xo-so-'+e+'.html?type=thongke" title="Thống kê kết quả điện toán"><input class="btninvedo" type="button" value="Thống Kê" style="margin-top:5px"/></a></td><td align="center">&nbsp;</td><td align="center">&nbsp;</td><td align="center"><a href="/thong-ke-xo-so-'+e+'.html?type=bieudo" title="Biểu đồ kết quả điện toán mega 6/45"><input class="btninvedo" type="button" value="Biểu Đồ" style="margin-top:5px"/></a></td><td align="center">&nbsp;</td></tr></table></form>');
        },
        width: 350,
        title: "Chọn loại thống kê"
    });
}

if (getCookie("smartview") == "off") {
    $(".pagebody").removeClass("respohnsive");
}
$(document).ready(function(e) {


    setActive("#cssmenu ul ");
    // Create responsive trigger
    // $('#cssmenu').prepend('');
	$(".navibar > li").hover(function(){
		$(this).children('.sub-nav').show();
	},function(){
		$(this).children('.sub-nav').hide();
	});
	
	$("header").before($("<div />", {class: "bg-overlay",}));
	$(".btn-top").click(function() {
		$(".topnav").slideToggle("fast");
		$(this).toggleClass("active");
	});
	$(".navimobile").click(function() {
		$(".navbar").slideToggle("fast");
		$(this).find(".btn-menu").toggleClass("active");
		$(".bg-overlay").fadeToggle("fast");
	});
	$(".drop").click(function() {
		$(this).parent().find(">ul").slideToggle("fast");
		$(this).toggleClass("active");
		$(this).parent("li").toggleClass("active");
	});
	$(".bg-overlay").click(removeStyle);
	$(window).resize(function(){
		if ($(window).width()>767) {
			removeStyle();
		};
		if($(window).width()>991) {
			removeStyle();
		}
	});
	
	$(".title_bottom").click(function(){
		if($(window).width() < 768){
			if($(this).hasClass('active')){
				$(".link-list").slideUp(100);
				$(this).removeClass('active');
			}
			else {
				$(".link-list").hide(100);
				$(".title_bottom").removeClass('active');
				$(this).addClass('active');
				$(this).parent().children(".link-list").slideDown(100);
			}
		}
	});
	
    $("#responsive-tab a").click(function(e) {
        $(this).toggleClass("clicked");
        $('#cssmenu').toggleClass('mobilemenushow');
		$("body").toggleClass("hideover");
        return false;
    });
    
	$(".ngaykqxstt").click(function(e){
		$("#getngaykqxs_1").focus();
	});

    $("#btn_onoffsmartview").click(function(e) {
        if (getCookie("smartview") == "off") {
            $(".pagebody").addClass("respohnsive");
            setCookie("smartview", "", -1);
        } else {
            $(".pagebody").removeClass("respohnsive");
            setCookie("smartview", "off", 7);
        }
    });

	$(".denled").click(function(e) {
		var id=$(this).attr('data-id');
		$.ajax({
			type: "GET",
			url: "/ajax/updateDenLed.php",
			data: "id=" + id,
			success: function(e) {
			}
		});
	});

    $(".btncloselototructiep").click(function(e) {
        var idt = $(this).attr("data-id");
        $(".box_dauduoitinh_" + idt).hide(300);
    });
    $(".box_sms").click(function(e) {
        window.open("/sms", "_sms")
    });

    setToolBkqxs();

    $(window).scroll(function() {
        if ($(this).scrollTop() > 100) {
            $(".scrollup").fadeIn()
        } else {
            $(".scrollup").fadeOut()
        }
    });
    $(".scrollup").click(function() {
        $("html, body").animate({
            scrollTop: 0
        }, 600);
        return false
    });
    $("#btnMenu_icon").click(function(e) {
        if ($(".leftmenu").hasClass("active")) {
            $(".leftmenu").animate({
                width: 0
            }, 300);
            $(".gridContainer").height("auto");
            $(".leftmenu").removeClass("active");
            $(".leftmenu").hide()
        } else {
            $(".leftmenu").show();
            var t = window.innerHeight;
            if (t < $(".leftmenu").height() + 50) t = $(".leftmenu").height() + 50;
            else $(".leftmenu").height(t - 50);
            $(".leftmenu").animate({
                width: "100%"
            }, 300);
            $(".gridContainer").height(t);
            $(".leftmenu").addClass("active")
        }
    });
    $(".btntkhdv").click(function(e) {
        var t = $(this).attr("data-id");
        if ($(this).hasClass("btnclicked")) {
            CloseLotoDonVi(t, t);
            $(this).removeClass("btnclicked");
			$(this).parent().children(".btnprintlogomien").hide();
        } else {
            getLotoDonVi(t, t);
            $(this).addClass("btnclicked");
			$(this).parent().children(".btnprintlogomien").show();
        }
    });
	
	$(".btnprintlogomien").click(function(e){
		printContent("DDM"+$(this).data("id"));
	});
	
    $(".btntk2sc").click(function(e) {
        var t = $(this).attr("data-id");
        if ($(this).hasClass("btnclicked")) {
			$(this).parent().children(".btnprintlogomien").hide();
            $("#loto_" + t).hide(500, null, function() {
                $("#loto_" + t).remove();
            });
            $(this).removeClass("btnclicked");
        } else {
            $("#DDM" + t).html('<div id="DDMfull' + t + '"><center><img src="/images/processing.gif"><br>Đang xử lý...<center></div>');
            $.ajax({
                type: "GET",
                url: "/ajax/tkloto2so.php",
                data: "get=" + t,
                success: function(e) {
                    $("#DDM" + t).html('<div id="loto_' + t + '">' + e + "</div>")
                    $(".btntkhdv[data-id='" + t + "']").removeClass("btnclicked");

                }
            });
            $(this).addClass("btnclicked");
			$(this).parent().children(".btnprintlogomien").show();
        }
    });
	
	$(".btntk2sc").click();
	
    $(".defaulttext").each(function() {
        if ($.trim(this.value) == "") {
            this.value = $(this).attr("title")
        } else {
            if ($.trim(this.value) != $(this).attr("title")) $("#" + $(this).attr("id")).addClass("removedefaulttext")
        }
        $(this).focus(function() {
            if (this.value == $(this).attr("title")) {
                this.value = "";
                $("#" + $(this).attr("id")).addClass("removedefaulttext")
            }
        });
        $(this).blur(function() {
            if (this.value == "") {
                $("#" + $(this).attr("id")).removeClass("removedefaulttext");
                this.value = $(this).attr("title")
            } else if (this.value == "") {
                $("#" + $(this).attr("id")).removeClass("removedefaulttext");
                this.value = "..."
            }
        })
    });

    $(".topmenu li a").click(function(e) {
        var submn = $(this).attr("rel");
        if ($(this).hasClass("active")) {
            $("#" + submn).hide(300);
            $(this).removeClass("active");
        } else {
            $(".top_submenu").hide();
            $(".topmenu .root a").removeClass("active");
            $("#" + submn).show(300);
            $(this).addClass("active");
        }

        return false;
    });
    $(function() {
        if (getCookie("username") != "") {
            if (getCookie("usgl") == "") {
                if (navigator.geolocation) {
                    setCookie("usgl", "1", 7);
                    navigator.geolocation.getCurrentPosition(SetUserLocation);
                } else {
                    setCookie("usgl", "0", 7);
                }
            }
        }

    });

});