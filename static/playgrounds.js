simplemde = null;
simplemde_container = null;
old_value = "";

function send_update(parent, new_value) {
    parent.toggleClass('loading', true);
    var id = parent.attr('id');
    var url = $( "#ajax-update" ).attr("url");
    var csrf = $( "#ajax-update" ).attr("csrf-token");
    var chunks = $( CHUNK_SELECTOR ).map( function(){
        return $( this ).attr("id");
    }).toArray();
    var envelope = {
        update_chunk: id,
        chunks: chunks,
        content: new_value
    };
    var post_data = {
        csrf_token: csrf,
        payload: JSON.stringify(envelope)
    };
    console.log("Post:");
    console.log(url);
    console.log(post_data);

    var posting = $.post( url, post_data );
    posting.done( function(data) {
        parent.children(".playground-chunk").html(data['content']);
        parent.children("textarea").html(new_value);
        parent.toggleClass('loading', false);
        MathJax.Hub.Queue(["Typeset",MathJax.Hub, parent.children(".playground-chunk")[0]]);
    });
}


function hide_mde() {
    if (simplemde_container) {
        var parent = $( simplemde_container );
        var section = parent.children(".playground-chunk");
        var textarea = parent.children("textarea");
        var new_value = simplemde.codemirror.getValue();
        simplemde.toTextArea();
        simplemde = null;
        section.toggleClass('invisible', false);
        simplemde_container = null;
        if (old_value.trim() != new_value.trim()) {
            send_update(parent, new_value)
        }
    }
}

function find_position(parent, source, node, offset) {
    var rel_position = parent.compareDocumentPosition(node);
    if (rel_position & Node.DOCUMENT_POSITION_CONTAINED_BY) {
        var pos = 0;
        console.log("Begin search");
        console.log(source);
        console.log(parent);
        var treeWalker = document.createTreeWalker(parent, NodeFilter.SHOW_TEXT, null, false);
        var currentNode;
        while (currentNode = treeWalker.nextNode()) {
            var text = currentNode.textContent;
            if (currentNode===node) {
                text = text.slice(0, offset);
            }
            text = text.trim();
            var spl = text.split();
            var word;
            var i;
            for (i = 0; i<spl.length; i++) {
                word = spl[i];
                if (word) {
                    console.log(word);
                    pos = source.indexOf(word, pos);
                    if (pos<0) {
                        return source.length;
                    }
                    pos += word.length;
                }
            }
            if (currentNode===node) {
                console.log(offset);
                console.log(text);
                if (offset===0 || currentNode.textContent[offset-1].trim()=="") {
                    while (pos<source.length && source[pos].trim()=="") {
                        pos ++;
                    }
                }
                console.log("Search returns");
                console.log(pos);
                return pos;
            }
        }
        console.log("Not found");
        return source.length;
    } else if (rel_position & Node.DOCUMENT_POSITION_FOLLOWING) {
        return source.length;
    }
    return 0;
}



function show_mde(container, use_selection) {
    if ($( container ).hasClass("loading")) {
        return null;
    }
    var sel = window.getSelection();
    console.log(sel);
    var anchor = sel.anchorNode;
    var anchorOffset = sel.anchorOffset;
    var focus = sel.focusNode;
    var focusOffset = sel.focusOffset;
    if (simplemde_container && simplemde_container!=container) {
        hide_mde();
    }
    if (!simplemde_container) {
        var parent = $( container );
        var section = parent.children(".playground-chunk");
        var textarea = parent.children("textarea");
        simplemde_container = container
        simplemde = new SimpleMDE({
            autofocus: true,
                element: textarea[0],
                spellChecker: false,
                toolbar: ["bold", "italic", "heading", "|",
                  "quote", "unordered-list", "ordered-list", "|",
                  "link", "table", "|",
                  "undo", "redo", "|",
                  "preview", "guide"
                ],
                status: false,
        });
        old_value = textarea.text();
        section.toggleClass('invisible', true);
        var i1 = 0;
        var i2 = 0;
        if (anchor) {
            var pos = find_position(section[0], textarea.text(), anchor, anchorOffset);
            if (pos>=0) {
                i1 = pos;
            }
        }
        if (focus) {
            var pos = find_position(section[0], textarea.text(), focus, focusOffset);
            if (pos>=0) {
                i2 = pos;
            }
        }
        console.log(i1);
        console.log(i2);
        simplemde.codemirror.doc.setSelection(simplemde.codemirror.doc.posFromIndex(i1),
                simplemde.codemirror.doc.posFromIndex(i2));
    }
}

CHUNK_SELECTOR = "#playground > .playground-chunk-container";

function new_id() {
    return "chunk" + new Date().getTime().toString() + "_" +
        Math.floor(1000000000*Math.random()).toString();
}

function mde_focus_next(edit=false) {
    sel = $(":focus").next();
    if (sel.length === 0) {
        $( "#playground" ).append($( "#playground-new-chunk" ).html());
        sel = $( CHUNK_SELECTOR ).last();
        sel.attr("id", new_id());
        playground_init_chunk(sel);
    }
    sel.focus();
    if (edit) {
        show_mde(sel[0]);
    }
}

function playground_init_chunk(obj) {
    obj.attr("tabindex", "0");
    obj.click(function(e) {
        console.log("Click");
        console.log(e);
        show_mde(this);
    });
    obj.on('keydown', function(e) {
        console.log(e);
        if(this!==simplemde_container) {
            if(e.key === "Enter" && !e.shiftKey) {
                show_mde(this);
                return false;
            }
            if(e.key === "ArrowUp") {
                $(":focus").prev().focus();
                return false;
            }
            if(e.key === "ArrowDown") {
                mde_focus_next(false);
                return false;
            }
            if(e.key === "Enter" && e.shiftKey) {
                mde_focus_next(true);
                return false;
            }
        }
        if(this===simplemde_container) {
            if(e.key === "Enter" && e.shiftKey) {
                hide_mde();
                this.focus();
                mde_focus_next(true);
                return false;
            }
            if(e.key === "Escape") {
                hide_mde();
                this.focus();
            }
        }
        return true;
    });
}

$( document ).ready(function () {
    $( ".playground-item-title" ).attr("contentEditable", "true");
    $( ".playground-item-title" ).on('input', function(e) {
        console.log(e);
    });
    $( ".playground-item-title" ).on('keydown', function(e) {
        if(e.key === "Escape") {
            mde_focus_next(false);
            return false;
        }
        if (e.key === "Enter") {
            mde_focus_next(true);
            return false;
        }
        if(e.key === "ArrowUp") {
            console.log("Up");
            $(":focus").prev().focus();
            return false;
        }
        if(e.key === "ArrowDown") {
            mde_focus_next(false);
            return false;
        }
        return true;
    });
    $( CHUNK_SELECTOR ).each( function() {
        playground_init_chunk($( this ));
        return true;
    });
    $( document ).click( function(e) {
        if (simplemde_container && simplemde_container.contains(e.target)) {
            return true;
        } else{
            hide_mde();
            return true;
        }
    });
    mde_focus_next(false);
});
