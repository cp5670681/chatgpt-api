import json
import os

from dotenv import load_dotenv
import requests

load_dotenv()


# 读取流式的可迭代对象，根据分隔符重新分割成生成器
def read_stream(iterable, split=b'\n\n'):
    chunk = b''
    for data in iterable:
        if not data:
            yield chunk
            break
        chunk += data
        while True:
            index = chunk.find(split)
            if index == -1:
                break
            yield chunk[:index]
            chunk = chunk[index + 1:]


class ChatgptApi:
    def __init__(self, authorization):
        self.authorization = authorization

    def login(self):
        ...

    def chat(self, question):
        print(self.authorization)
        url = 'https://chat.openai.com/backend-api/conversation'
        headers = {
            'accept': 'text/event-stream',
            'accept-language': 'zh-CN,zh;q=0.9',
            'authorization': self.authorization,
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://chat.openai.com',
            'pragma': 'no-cache',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        body = {
            "action": "next",
            "messages": [
                {
                    "author": {
                        "role": "user"
                    },
                    "content": {
                        "content_type": "text",
                        "parts": [question]
                    },
                    "metadata": {}
                }
            ],
            "parent_message_id": "",
            "model": "text-davinci-002-render-sha",
            "timezone_offset_min": -480,
            "suggestions": [],
            "history_and_training_disabled": False,
            "conversation_mode": {
                "kind": "primary_assistant"
            },
            "force_paragen": False,
            "force_rate_limit": False
        }
        response = requests.post(url, json=body, headers=headers, stream=True)
        print(response.status_code)

        streams = read_stream(response.iter_content(chunk_size=1024))
        streams = list(streams)
        # 获取最后一条回答
        last_answer_bytes = streams[-3]
        # 回答转json
        last_answer = json.loads(last_answer_bytes.decode('utf-8').strip()[6:])
        result = last_answer['message']['content']['parts'][0]
        return result


if __name__ == '__main__':
    gpt = ChatgptApi(os.getenv('AUTHORIZATION'))
    prompt = 'You are PR-Reviewer, a language model designed to review a Git Pull Request (PR).\nYour task is to provide constructive and concise feedback for the PR, and also provide meaningful code suggestions.\nThe review should focus on new code added in the PR diff (lines starting with \'+\')\n\nExample PR Diff:\n======\n## file: \'src/file1.py\'\n\n@@ -12,5 +12,5 @@ def func1():\ncode line 1 that remained unchanged in the PR\ncode line 2 that remained unchanged in the PR\n-code line that was removed in the PR\n+code line added in the PR\ncode line 3 that remained unchanged in the PR\n\n@@ ... @@ def func2():\n...\n\n\n## file: \'src/file2.py\'\n...\n======\n\n\nCode suggestions guidelines:\n- Provide up to 4 code suggestions. Try to provide diverse and insightful suggestions.\n- Focus on important suggestions like fixing code problems, issues and bugs. As a second priority, provide suggestions for meaningful code improvements like performance, vulnerability, modularity, and best practices.\n- Avoid making suggestions that have already been implemented in the PR code. For example, if you want to add logs, or change a variable to const, or anything else, make sure it isn\'t already in the PR code.\n- Don\'t suggest to add docstring, type hints, or comments.\n- Suggestions should focus on the new code added in the PR diff (lines starting with \'+\')\n- When quoting variables or names from the code, use backticks (`) instead of single quote (\').\n\n\nThe output must be a YAML object equivalent to type $PRReview, according to the following Pydantic definitions:\n=====\n\nclass Review(BaseModel):\n    estimated_effort_to_review_[1-5]: str = Field(description="Estimate, on a scale of 1-5 (inclusive), the time and effort required to review this PR by an experienced and knowledgeable developer. 1 means short and easy review , 5 means long and hard review. Take into account the size, complexity, quality, and the needed changes of the PR code diff. Explain your answer in a short and concise manner.")\n    relevant_tests: str = Field(description="yes\\no question: does this PR have relevant tests added or updated ?")\n    possible_issues: str = Field(description="Does this PR code introduce clear issues, bugs, or major performance concerns? If there are no apparent issues, respond with \'No\'. If there are any issues, describe them briefly. Use bullet points if more than one issue. Be specific, and provide examples if possible. Start each bullet point with a short specific header, such as: "- Possible Bug: ...", etc.")\n    security_concerns: str = Field(description="does this PR code introduce possible vulnerabilities such as exposure of sensitive information (e.g., API keys, secrets, passwords), or security concerns like SQL injection, XSS, CSRF, and others ? Answer \'No\' if there are no possible issues. If there are security concerns or issues, start your answer with a short header, such as: \'Sensitive information exposure: ...\', \'SQL injection: ...\' etc. Explain your answer. Be specific and give examples if possible")\n\nclass CodeSuggestion(BaseModel):\n    relevant_file: str = Field(description="the relevant file full path")\n    language: str = Field(description="the language of the relevant file")\n    suggestion: str = Field(description="a concrete suggestion for meaningfully improving the new PR code. Also describe how, specifically, the suggestion can be applied to new PR code. Add tags with importance measure that matches each suggestion (\'important\' or \'medium\'). Do not make suggestions for updating or adding docstrings, renaming PR title and description, or linter like.")\n    relevant_line: str = Field(description="a single code line taken from the relevant file, to which the suggestion applies. The code line should start with a \'+\'. Make sure to output the line exactly as it appears in the relevant file")\n\nclass PRReview(BaseModel):\n    review: Review\n    code_feedback: List[CodeSuggestion]\n=====\n\n\nExample output:\n```yaml\nreview:\n  estimated_effort_to_review_[1-5]: |\n    3, because ...\n  relevant_tests: |\n    No\n  possible_issues: |\n    No\n  security_concerns: |\n    No\ncode_feedback\n- relevant_file: |\n    directory/xxx.py\n  language: |\n    python\n  suggestion: |\n    xxx [important]\n  relevant_line: |\n    xxx\n```\n\nAnswer should be a valid YAML, and nothing else. Each YAML output MUST be after a newline, with proper indent, and block scalar indicator (\'|\')'
    code = 'PR Info:\n\nTitle: \'[SC-2480]1.释放校验修改 2.关闭释放leads给销售总监\'\n\nBranch: \'yang/SC-2480\'\n\nDescription:\n======\nCloses SC-2480\n======\n\n\nThe PR Diff:\n======\n## app/controllers/api/omni_api_controller.rb\n\n@@ -137,39 +137,39 @@ class Api::OmniApiController < ActionController::Base\n    # 要释放的leads\n     leads = CustomerFirmLead.find_by_id(params[:leads_id])\n     return error_json({:can_extend => false}, "Leads不存在") if leads.blank?\n     # 操作人\n-    action_user = Employee.find_by_id(params[:employee_id])\n+    # action_user = Employee.find_by_id(params[:employee_id])\n     # 申请人\n     apply_user = Employee.find_by_id(params[:apply_id])\n     firm = leads.customer_firm\n     # 申请的按钮展示权限\n-    if firm.archived? && !firm.show_leads_release?(apply_user)\n-      return error_json({:can_release => false}, \'无权释放按钮展示权限\')\n-    end\n+    # if firm.archived? && !firm.show_leads_release?(apply_user)\n+    #   return error_json({:can_release => false}, \'无权释放按钮展示权限\')\n+    # end\n     if params[:is_apply].to_i == 1 && ApplyReleaseLead.exists?([\'customer_firm_id = ? and approved_status = 1 and sales_id = ?\', firm.id, apply_user.id])\n       return error_json({:can_release => false}, \'无权释放按钮展示权限，该公司已有待审批的释放申请\')\n     end\n-    lead_ids = firm.leads.select{|lead| (action_user.max_auth_level >= RccOrgAuth::Level::MANAGER ||\n-      !lead.in_cce_stage?) || \n-      (lead.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid] && ::Department::PRICE_CCE_IDS.include?(action_user.department_id))\n-    }.select { |l| l.sales_id.to_i > 0 && \n-      (l.sales_id == action_user.id || \n-        action_user.is_leader_or_manager_of?(l.sales_id)) || \n-        (l.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid] && ::Department::PRICE_CCE_IDS.include?(action_user.department_id))\n-      }.map { |l| l.leads_type_id }\n+    # lead_ids = firm.leads.select{|lead| (action_user.max_auth_level >= RccOrgAuth::Level::MANAGER ||\n+    #   !lead.in_cce_stage?) || \n+    #   (lead.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid] && ::Department::PRICE_CCE_IDS.include?(action_user.department_id))\n+    # }.select { |l| l.sales_id.to_i > 0 && \n+    #   (l.sales_id == action_user.id || \n+    #     action_user.is_leader_or_manager_of?(l.sales_id)) || \n+    #     (l.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid] && ::Department::PRICE_CCE_IDS.include?(action_user.department_id))\n+    #   }.map { |l| l.leads_type_id }\n \n-    return error_json({:can_release => false}, \'没有该leads的释放权限\') if !lead_ids.include?(leads.leads_type_id)\n+    # return error_json({:can_release => false}, \'没有该leads的释放权限\') if !lead_ids.include?(leads.leads_type_id)\n \n     # 释放公司leads&&释放原因为重复公司时,需要校验公司当前跟进人（去重）数是否大于2\n-    if params[:reason_id].to_i == ::NoRenewNote::NO_RENEW_REASONS_HASH[:repeat_firm]\n-      sales_count = CustomerFirmLead.count(:select=> "distinct sales_id",:conditions => ["firm_id = ? and nvl(sales_id, 0) > 0", leads.firm_id])   \n-      return error_json({:can_release => false}, \'公司还有其他人跟进，无法归档\') if sales_count >= 2\n-    end\n+    # if params[:reason_id].to_i == ::NoRenewNote::NO_RENEW_REASONS_HASH[:repeat_firm]\n+    #   sales_count = CustomerFirmLead.count(:select=> "distinct sales_id",:conditions => ["firm_id = ? and nvl(sales_id, 0) > 0", leads.firm_id])   \n+    #   return error_json({:can_release => false}, \'公司还有其他人跟进，无法归档\') if sales_count >= 2\n+    # end\n     # 自己的leads或者是自己队员的leads可以直接释放,客服部可以释放慧招采\n-    if action_user.id == leads.sales_id || action_user.is_leader_or_manager_of?(leads.sales_id) || action_user.icc_service? && leads.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid]\n-      return success_json({:can_release => true}, \'允许释放\')\n-    end\n+    # if action_user.id == leads.sales_id || action_user.is_leader_or_manager_of?(leads.sales_id) || action_user.icc_service? && leads.leads_type_id == ::CustomerFirmLead::LEADS_TYPE[:bid]\n+    #   return success_json({:can_release => true}, \'允许释放\')\n+    # end\n \n     success_json({:can_release => true})\n   end\n\n\n\n\n## app/views/sales/firm_show.html.erb\n\n@@ -416,10 +416,12 @@ \n    <% if current_user.can_send_declare_letter?(@firm) %>\n       <%= button_to_function \'发送声明信\', "open_url(\'/sales/send_tks_letter/#{@firm.id}?type=#{TksLetter::TYPE_HASH[:declare]}\')", :class => \'searchButton\' -%>\n     <% end %>\n     <% l_id = current_user.has_firm_leads_and_is_cce_manager(@firm.id) -%>\n-    <% if l_id %>\n-        <%= button_to_function \'释放leads给销售总监\', "release_leads_to_sale_director(#{@firm.id})", :class => \'searchButton\' -%>\n+    <% if ::Base::ControlOperationPermiss.check_employee_operation(\'release_leads_to_sales_director\', current_user.id) %>\n+      <% if l_id %>\n+          <%= button_to_function \'释放leads给销售总监\', "release_leads_to_sale_director(#{@firm.id})", :class => \'searchButton\' -%>\n+      <% end %>\n     <% end %>\n     <% if (@firm.is_succeed_publish?) && (@is_it || @is_bid_develop_member) -%>\n         <%= button_to_function \'设为推荐\',"set_bid_recommend(#{@firm.id},this)",:class => \'searchButton\',:id => \'btn_set_bid_firm_recommend\' if @has_bid_firm_recommend && @firm.lead_bid_by?(current_user.id)%>\n        <%= button_to_function \'再次推荐\',"set_bid_recommend(#{@firm.id},this)",:class => \'searchButton\',:id => \'btn_set_bid_firm_recommend\' if @firm.can_next_recommend?(current_user)%>\n======\n\n\nResponse (should be a valid YAML, and nothing else):\n```yaml'
    question = f'{prompt}\n{code}\n请用中文回答！'
    print(gpt.chat(question))
