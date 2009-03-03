# == Schema Information
#
# Table name: profile_extensions
#
#  id           :integer(4)      not null, primary key
#  extension_id :integer(4)
#  profile_id   :integer(4)
#  version      :string(255)
#  created_at   :datetime
#  updated_at   :datetime
#

class ProfileExtension < ActiveRecord::Base
  belongs_to :extension
  belongs_to :profile
end
