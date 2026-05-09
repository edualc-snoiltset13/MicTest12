package com.abc_bank.abc_bank.auth_users.dtos;


import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdatePasswordRequest {
    @NotBlank(message="old password is required")
    private String oldPassword;

    @NotBlank(message="new password is required")
    private String newPassword;
}
