; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun current_chain_id () Int)
(declare-fun deployment_chain_id () Int)
(declare-fun domain_separator_cached () Bool)
(declare-fun signatures_generated_on_new_chain () Bool)
(declare-fun signature_valid () Bool)
(assert
 (= current_chain_id current_chain_id))
(assert
 (= deployment_chain_id deployment_chain_id))
(assert
 (= domain_separator_cached domain_separator_cached))
(assert
 (= signatures_generated_on_new_chain signatures_generated_on_new_chain))
(assert
 (= signature_valid signature_valid))
(define-fun report_preconditions () Bool (and domain_separator_cached
     (distinct current_chain_id deployment_chain_id)
     signatures_generated_on_new_chain))
(define-fun report_safety () Bool (=> (distinct current_chain_id deployment_chain_id) (not (not signature_valid))))
(define-fun report_effects () Bool (and (distinct current_chain_id deployment_chain_id) (not signature_valid)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
