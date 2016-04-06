% include('global/header.tpl', title=name)
<div class="container">
    <div class="starter-template">
        <div class="well well-lg">
            <h1>{{name}} ({{type}})</h1>
            <p id="counterVal" style="font-size: 42px;">
                <pre>
% for rec in records:
    {{rec}}
% end
</pre>
            </p>
        </div>
        
        <div class="panel panel-primary">
            <div class="panel-heading">
                <h3 class="panel-title">Need to script it?</h3>
            </div>
            <div class="panel-body">
                <p>
                Verify the results using curl:
                </p>
                <pre>curl https://dnsjson.com/{{name}}/{{type}}.json</pre>

                <p>
                Need the results in plain text?
                </p>
                <pre>curl https://dnsjson.com/{{name}}/{{type}}.txt</pre>
            </div>
        </div>
        
        <div class="panel panel-primary">
            <div class="panel-heading">
                <h3 class="panel-title">Need to lookup something else?</h3>
            </div>
            <div class="panel-body">
                <form class="form-inline" method="POST" action="/">
                    <fieldset>
                        <div class="form-group">
                            <input type="text" name="recordName" class="form-control" id="recordName"
                                placeholder="{{name}}">
                        </div>
                        <div class="form-group">
                            <select class="form-control" id="recordType" name="recordType">
                                <option>Type</option>
                                % for type in recTypes:
                                    <option>{{type}}</option>
                                %end
                            </select>
                        </div>
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">Lookup</button>
                        </div>
                    </fieldset>
                </form>
            </div>
        </div>

    </div>
</div>
% include('global/footer.tpl')