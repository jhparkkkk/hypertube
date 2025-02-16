require 'sinatra'
require 'dotenv/load'

set :bind, '0.0.0.0'

get '/' do
  "OmniAuth service is running!"
end
