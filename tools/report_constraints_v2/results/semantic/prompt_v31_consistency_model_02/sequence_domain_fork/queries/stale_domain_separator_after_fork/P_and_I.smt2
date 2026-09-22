; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun current_chain_id () Int)
(declare-fun cached_chain_id () Int)
(declare-fun validated_chain_id () Int)
(declare-fun signature_from_current_chain () Bool)
(declare-fun signature_valid () Bool)
(declare-fun intent_flow_enabled () Bool)
(assert
 (= current_chain_id current_chain_id))
(assert
 (= cached_chain_id cached_chain_id))
(assert
 (= validated_chain_id validated_chain_id))
(assert
 (= signature_from_current_chain signature_from_current_chain))
(assert
 (= signature_valid signature_valid))
(assert
 (= intent_flow_enabled intent_flow_enabled))
(define-fun report_preconditions () Bool (distinct current_chain_id cached_chain_id))
(define-fun report_safety () Bool (=> signature_from_current_chain
    (and (= validated_chain_id current_chain_id) signature_valid)))
(define-fun report_effects () Bool (and signature_from_current_chain
     (not signature_valid)
     (not intent_flow_enabled)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
