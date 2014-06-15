function fullscreen(e) {
	if (RunPrefixMethod(document, "FullScreen") || RunPrefixMethod(document,
		"IsFullScreen")) {
		$("#overlay").prependTo($("body")).css("background-color","rgba(0,0,0,1)");
		RunPrefixMethod(document, "CancelFullScreen");
	} else {
		$("#overlay").prependTo($("#sigma-example")).css("background-color","rgba(0,0,0,0.8)");
		RunPrefixMethod(e, "RequestFullScreen");
		setTimeout( sigInst.position(0,0,1).draw(), 1000)
		
	}
}

function exportImage() {
	data = {}
	$("canvas").each(function () {
		data[$(this).attr("id")] = this.toDataURL();
	});
	$.post("combineImages.py", data, function(b64) {
		url = "data:image/png;base64,"+b64
		console.log(url)
		window.open(url)
	});
}

// Fullscreen code
var pfx = ["webkit", "moz", "ms", "o", ""];

function RunPrefixMethod(obj, method) {
	var p = 0,
		m, t;
	while (p < pfx.length && !obj[m]) {
		m = method;
		if (pfx[p] == "") {
			m = m.substr(0, 1).toLowerCase() + m.substr(1);
		}
		m = pfx[p] + m;
		t = typeof obj[m];
		if (t != "undefined") {
			pfx = [pfx[p]];
			return (t == "function" ? obj[m]() : obj[m]);
		}
		p++;
	}
}

$(function () {
	var e = document.getElementById("sigma-example");
	var b = document.getElementById("fs_button");
	var overlay = document.getElementById("overlay")
	e.ondblclick = function () {
		fullscreen(e)
	}
	b.onclick = function () {
		fullscreen(e)
	}

	$(document).keypress(function (e) {
		if (e.charCode == 101) {
			exportImage();
		}
	});
	
	$(e).width( $("#graph-wrapper").width() - 20 - $("#sidebar").width() );
	
	$("input[type='text'],input[type='password'],textarea").wijtextbox();
	$("select").wijdropdown();
	$("input[type='radio']").wijradio();
	$("input[type='checkbox']").wijcheckbox();
	$("button, input[type='submit']").button();
	$("div[type='superpanel']").wijsuperpanel({
				height: $(this).height(),
				autoRefresh: true,
				vScroller: {
					scrollBarVisibility: 'auto',
					scrollMode: 'scrollbar'
                },
				hScroller: {
					scrollBarVisibility: 'hidden',
					scrollMode: 'scrollbar'
                }
				});

	$("#export_image").click(exportImage);

	
	// Legend
	$.getJSON("../../BackEnd/ElegantWebApi/data", {"model":"NodeType"}, function(data) {
		legendHTML = "<ul>"
		for( d in data ) {
			legendHTML += "<li name='"+data[d]["id"]+"'><div class='legendSquare category visible' style='background:" + 
						   data[d]["color"]+ ";'></div>" + data[d]["name"] +
						   "</li>"
		}	
		legendHTML += "</ul>"
		$("#legend").html(legendHTML)
	});
	
	$("#nodeinfo li").click(function() {
		$("#nodeinfo li").not($(this).fadeOut())
	});
	
	$("#threshold").change(function(e) {
		$("#overlay").fadeIn(300, function() { 
			t = $("#threshold option[selected=selected]").val()
			
			if ($("#level").val() == "on" ){
				depth = 1
			} else {
				depth = 0
			}
			init(t, currentNode, depth)
			
		});
	});
	
	$("#mainview").click(function(e) {
		c = window.confirm( "This will take a long time to render, are you certain you'd like to proceed?" )
		if( !c ) {
			return false;
		}
		$("#overlay").fadeIn(300, function() { 
			t = $("#threshold option[selected=selected]").val()
			init(t, false, -1)
		});
	});
	
	$(document).on("click", "#onlythis", function(e) {
		$("#overlay").fadeIn(300, function() {
			t = $("#threshold option[selected=selected]").val()
			node = $("#onlythis").attr("name")
			if ($("#level").prop('checked') ){
				depth = 1
			} else {
				depth = 0
			}
			init(t, node, depth)
		});
		return false;
	});
	
	$(document).on("click", ".category", function(e) {
		$(this).toggleClass("visible")
	
		
		type = parseInt($(this).parent("li").attr("name"))
		
		sigInst.iterNodes(function (n) {
			ntype = parseInt(n['attr']['attributes'][0].val)
			
			if( type == ntype ) {
				n.hidden = !n.hidden;
			}
		});
		sigInst.draw()
		
		return false
	});
	
	$(document).on("click", "#closenodemenu", function(e) {
		$("#nodemenu").fadeOut(300);
	});
	
	$(document).on("click", ".details", function(e) {
		n1 = $(this).attr("name")
		n2 = $(this).parents("ul").attr("name")
		nc = n1 + "||"+ n2
		
		selected = this
		articlesElement = $(selected).parents("li").find(".articles")
		
		if(articlesElement.length > 0) { // Articles were loaded
			
			console.log("Loaded articles")
			
			if (articlesElement.is(":visible")) {
				$(selected).text("+")
				articlesElement.slideUp(300)
			} else {
				$(selected).text("-")
				articlesElement.slideDown(300)
			}

				
		} else { // Articles weren't loaded
			
			console.log("Loading articles")
			
			$(selected).text("-")
			
			$.getJSON("../../BackEnd/ElegantWebApi/data", {"model":"Edge", "source":nc, "end":nc, "limit":1}, function(data) {
				edges = []
				for( edge in data) {
					edges.push(data[edge].id)
				}
				$.getJSON("../../BackEnd/ElegantWebApi/data", {"model":"EdgeArt", "edge":edges.join("||")}, function(data) {
					articles = []
					
					for(article in data) {
						art = data[article].article
						
						if(articles.indexOf(art) < 0) {
							articles.push(art)
						}
						
					}
					
					$.getJSON("../../BackEnd/ElegantWebApi/data", {"model":"Article", "id":articles.join("||"), "limit":10}, function(data) {
						articlesList = $("<ul>").attr("class","articles")
						for( art in data ) {
							li = $("<li>").html("<a href='http://www.ncbi.nlm.nih.gov/pubmed/"+data[art].id+"' target='_blank' title='"+data[art].title+"'>"+ data[art].title.substring(0,32) +"...</a>")
							li.appendTo( articlesList )
						}
						last = $("<li>").html("<a href='../../BackEnd/ElegantWebApi/data/?model=Article&id="+articles.join("||")+"' target='_blank'>Get all articles</a>")
						last.appendTo(articlesList)
						
						articlesList.appendTo($(selected).parents("li"))
						articlesList.slideDown(300)
					});				
				});
			});
			
		}
	});
	
	init()
	
})

