# == Schema Information
#
# Table name: profiles
#
#  id         :integer(4)      not null, primary key
#  user_id    :integer(4)
#  name       :string(255)
#  secret     :string(255)
#  os         :string(255)
#  version    :string(255)
#  platform   :string(255)
#  created_at :datetime
#  updated_at :datetime
#

class Profile < ActiveRecord::Base
  belongs_to :user
  has_many :profile_extensions

  def before_create
    secret_uuid = uuid.uuid4()
  end

end
