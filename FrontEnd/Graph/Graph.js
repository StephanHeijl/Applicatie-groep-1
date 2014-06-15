currentNode = "";

function init(t, node, depth) {
	$("#nodemenu").fadeOut(300); 
	
	$(".category").addClass("visible");
	
	if (t == undefined ){
		t = 0;
	}
	if (node == undefined ){
		if (window.location.search.length > 1 ) {
			node = window.location.search.substring(1);
			currentNode = node;
			depth=0;
		} else {
			node = false;
		}
	}
	if( depth == undefined ){
		depth = -1;
	}
	
	if(typeof sigInst == 'undefined' ) {
		// Instanciate sigma.js and customize rendering :
		sigInst = sigma.init(document.getElementById('sigma-example')).drawingProperties({
			defaultLabelColor: '#000',
			defaultLabelSize: 13,
			defaultLabelBGColor: '#000',
			defaultLabelHoverColor: '#000',
			labelThreshold: 10,
			defaultNodeColor: '#fff',
			defaultEdgeType: 'undirected',
		}).graphProperties({
			minNodeSize: 2,
			maxNodeSize: 30,
			minEdgeSize: 1,
			maxEdgeSize: 40
		}).mouseProperties({
			minRatio: 0.1,
			maxRatio: 100
		});
	} else {
		sigInst.emptyGraph()
	}
	
	// Parse a GEXF encoded file to fill the graph
	// (requires "sigma.parseGexf.js" to be included)
	$("#loadinginfo").text( "Downloading/Parsing graph file. This may take some time." )
	
	setTimeout(function() {
		url = 'http://cytosine.nl/~owe8_pg1/Applicatie/BackEnd/ElegantWebApi/graph?threshold='+t+'&node='+node+'&depth='+depth
		$("#export_xml").click(function() {
			url = 'http://cytosine.nl/~owe8_pg1/Applicatie/BackEnd/ElegantWebApi/graph?threshold='+t+'&node='+node+'&depth='+depth
			win = window.open(url, "_blank")
			win.focus()
		});
		
		sigInst.parseGexf(url);
		sigInst.position(0,0,1).draw()
	
		nodeCount = 0	
		sigInst.iterNodes(function (n) {
			n.size += (n.inDegree + n.outDegree)
			n.color = n['attr']['attributes'][2].val
			nodeCount+=1
		})
		
		sigInst.bind('downnodes',nodeClick).draw();	
		
		sigInst.iterEdges(function(e) {
				e.color = e['attr']['attributes'][1].val
				e.size = e['attr']['attributes'][2].val
		})
		
		// Draw the graph :
		sigInst.draw();
		$("#loadinginfo").text("Aligning nodes and edges")
		sigInst.startForceAtlas2();
		
		if( node && depth == 0 ) {
			t = 2000
		} else {
			t = 0.15*nodeCount * 1000
			if (t > 20000) {
				t = 20000
			}
		}
		
		setTimeout(function () {
			sigInst.stopForceAtlas2();

			function attributesToString(attr) {
				return '' +
					attr.map(function (o) {
					return '' + o.attr + ' : ' + o.val + '';
				}).join('') +
					'';
			}
			
			  var greyColor = '#666';
			  sigInst.bind('overnodes',function(event){
				var nodes = event.content;
				var neighbors = {};
				sigInst.iterEdges(function(e){
				  if(nodes.indexOf(e.source)<0 && nodes.indexOf(e.target)<0){
					if(!e.attr['grey']){
					  e.attr['true_color'] = e.color;
					  e.color = greyColor;
					  e.attr['grey'] = 1;
					}
				  }else{
					e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
					e.attr['grey'] = 0;
			 
					neighbors[e.source] = 1;
					neighbors[e.target] = 1;
				  }
				}).iterNodes(function(n){
				  if(!neighbors[n.id]){
					if(!n.attr['grey']){
					  n.attr['true_color'] = n.color;
					  n.color = greyColor;
					  n.attr['grey'] = 1;
					}
				  }else{
					n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
					n.attr['grey'] = 0;
				  }
				}).draw(2,2,2);
			}).bind('outnodes', function () {			
				sigInst.iterEdges(function (e) {
					e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
					e.attr['grey'] = 0;
				}).iterNodes(function (n) {
					n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
					n.attr['grey'] = 0;
					n.forceLabel = false;
				}).draw(2, 2, 2);
			});
			
			$("#overlay").fadeOut(300)
		}, t)
	
	}, 800);
}

function nodeClick(event) {
	node = event['content'][0]
	var nodeObj;
	sigInst.iterNodes(function(n){
		nodeObj = n;
	},[event.content[0]]);
	
	nodeInfo = "Node '"+node+"' is connected to: \n<ul name='"+nodeObj['attr']['attributes'][1].val+"'>"
				
	ot = $("<button>").text("Focus on this node").attr({"name": node, "id": "onlythis"})
	spinner = $("<input>").attr({"name":"depth", "type":"checkbox", "id":"level"}).css({"display":"inline-block"})
	
	var nodes = event.content;
	var neighbors = {};
	sigInst.iterEdges(function (e) {
		if (nodes.indexOf(e.source) == 0 || nodes.indexOf(e.target) == 0) {
			neighbors[e.source] = [e.color, e['attr']['attributes'][2].val];
			neighbors[e.target] = [e.color, e['attr']['attributes'][2].val];
		}
	}).iterNodes(function (n) {
		if (neighbors[n.id] && n.id != node) {
			nodeInfo += "<li style='color: "+n.color+"; '>\
						 <div class='legendSquare details' style='background:"+ neighbors[n.id][0] + ";' name='"+n['attr']['attributes'][1].val+"'> + </div>" +
						 n.id + ": "+ neighbors[n.id][1] + 
						 "</li>"
		}
	})
	
	$("#nodeinfo, #nodemenu").html("")
	$("#nodeinfo").append(ot)
	$("#nodemenu").append($("<button>").text("Close").attr({"id":"closenodemenu", "title":"Close node menu"}).button());

	$("#nodemenu").append(ot).fadeIn(300).css({"top": nodeObj.displayY, "left": nodeObj.displayX})
	$("#nodemenu").append("<br />Depth search ")
	$("#nodemenu").append(spinner)
	
	ot.button()
	spinner.wijcheckbox()
	$("#nodeinfo").append( nodeInfo + "</ul>")
	
}