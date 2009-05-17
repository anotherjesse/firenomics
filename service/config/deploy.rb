begin
  require 'capistrano_colors'
rescue
end

set :application, "firenomics"

set :deploy_to, "/home/deploy/firenomics"
set :deploy_via, :remote_cache
set :branch, 'master'
set :repository, "git@github.com:anotherjesse/firenomics.git"
set :scm, :git
set :git_shallow_clone, 1

set :user, 'deploy'
set :use_sudo, false

role :app, 'escher.userscripts.org'
role :web, 'escher.userscripts.org'
role :db,  'escher.userscripts.org', :primary => true

set :rails_env, 'production'

ssh_options[:paranoid] = false

desc "copy config files in after deploy"
task :after_update_code do
  run "cp #{shared_path}/config/*.yml #{release_path}/config/"
end

namespace :deploy do
  desc "restart passenger"
  task :restart, :roles => :app do
    run "touch #{current_path}/tmp/restart.txt"
  end

  namespace :web do

    desc "Serve up a custom maintenance page."
    task :disable, :roles => :web do
      require 'erb'
      on_rollback { run "rm #{shared_path}/system/maintenance.html" }

      reason      = ENV['REASON']
      deadline    = ENV['UNTIL']

      template = File.read("app/views/admin/maintenance.html.erb")
      page = ERB.new(template).result(binding)

      put page, "#{shared_path}/system/maintenance.html",
                :mode => 0644
    end
  end
end
