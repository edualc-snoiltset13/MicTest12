package com.abc_bank.abc_bank.auth_users.services;

import com.abc_bank.abc_bank.auth_users.dtos.LoginRequest;
import com.abc_bank.abc_bank.auth_users.dtos.LoginResponse;
import com.abc_bank.abc_bank.auth_users.dtos.RegistrationRequest;
import com.abc_bank.abc_bank.auth_users.dtos.ResetPasswordRequest;
import com.abc_bank.abc_bank.auth_users.dtos.UpdatePasswordRequest;
import com.abc_bank.abc_bank.auth_users.dtos.UserDTO;
import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.res.Response;

public interface UserService {

    Response<UserDTO> registerUser(RegistrationRequest request);

    Response<LoginResponse> loginUser(LoginRequest request);

    Response<UserDTO> getCurrentUser();

    Response<UserDTO> getUserById(Long id);

    Response<?> updatePassword(UpdatePasswordRequest request);

    Response<?> requestPasswordReset(String email);

    Response<?> resetPassword(ResetPasswordRequest request);

    User getCurrentUserEntity();
}
