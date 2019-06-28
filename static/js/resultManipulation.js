function sort(sorting, ordering){
	var urlQueryHeader = getQueryHeader(window.location.href);
    var url = window.location.href.replace(urlQueryHeader,'/sortBy');
    var sortIndex = url.indexOf('&sort');
    var filterIndex = url.indexOf('&filter');
    var extractURL = sortIndex==-1?url:sortIndex>filterIndex?url.substring(0,sortIndex):url.substring(0,sortIndex)+url.substring(filterIndex);
    window.open(extractURL+"&sort=sort_by+"+sorting+"%order_by+"+ordering, '_self');    		
}

function saveFavorites(userID){
	var url = window.location.href;
	var queryHeader = getQueryHeader(url);
	url = url.replace(queryHeader, "/favorites");
	var saveIndex = url.indexOf('&save');
	var url = saveIndex==-1?url:url.substring(0, saveIndex);
	window.open(url + "&save=" + userID, '_self');
}

function getQueryHeader(url){
	var endIndex = url.indexOf('?');
	var startIndex = url.lastIndexOf('/');
	return url.substring(startIndex, endIndex);
}