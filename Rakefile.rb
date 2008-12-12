require 'yaml'
require 'aws/s3'
require "active_support"

task :xpi do
  `rm -rf tmp/xpi`
  `mkdir -p tmp/xpi`
  `cp -r extension/. tmp/xpi`
  `rm tmp/xpi/.gitignore`

  build = "0.1.#{Time.now.to_i}"
  `cd tmp/xpi && sed -i 's/BUILD/#{build}/g' *.rdf`
  `cd tmp/xpi && find chrome chrome.manifest install.rdf | egrep -v "(~|#)" | xargs zip firenomics.xpi`
  puts "Built version #{build}"
end

task :release => :xpi do
  begin
      keys = YAML::load_file("s3.yml")['connection'].symbolize_keys
  rescue
    raise "Could not load AWS s3.yml"
  end

  AWS::S3::Base.establish_connection!(keys)

  [{:file => 'tmp/xpi/firenomics.xpi', :content_type => 'application/x-xpinstall'},
   {:file => 'tmp/xpi/update.rdf', :content_type => 'text/xml'}].each do |f|
    AWS::S3::S3Object.store(File.basename(f[:file]), open(f[:file]), 'firenomics', :access => "public-read", :content_type => f[:content_type])
  end

  puts "Uploaded to S3"
end

task :default => :release
